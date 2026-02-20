"""CostPilot — EC2 & RDS Rightsizing Recommendations.

Analyzes CloudWatch CPU/memory metrics and recommends
downsizing underutilized instances.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from .config import Config

logger = logging.getLogger(__name__)

# EC2 instance pricing (us-east-1 On-Demand, approximate)
EC2_PRICING = {
    "t3.nano": 0.0052, "t3.micro": 0.0104, "t3.small": 0.0208,
    "t3.medium": 0.0416, "t3.large": 0.0832, "t3.xlarge": 0.1664,
    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384,
    "m6i.large": 0.096, "m6i.xlarge": 0.192, "m6i.2xlarge": 0.384,
    "c5.large": 0.085, "c5.xlarge": 0.170, "c5.2xlarge": 0.340,
    "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504,
}

DOWNSIZE_MAP = {
    "t3.xlarge": "t3.large", "t3.large": "t3.medium", "t3.medium": "t3.small",
    "m5.2xlarge": "m5.xlarge", "m5.xlarge": "m5.large",
    "m6i.2xlarge": "m6i.xlarge", "m6i.xlarge": "m6i.large",
    "c5.2xlarge": "c5.xlarge", "c5.xlarge": "c5.large",
    "r5.2xlarge": "r5.xlarge", "r5.xlarge": "r5.large",
}


class RightSizer:
    """Analyze EC2 instances and recommend rightsizing."""

    def __init__(self, config: Config) -> None:
        self.session = config.get_session()
        self.ec2 = self.session.client("ec2")
        self.cw = self.session.client("cloudwatch")

    def analyze(self, cpu_threshold: float = 30.0, days: int = 14) -> dict[str, Any]:
        """Analyze all running EC2 instances for rightsizing."""
        instances = self._get_running_instances()
        logger.info(f"Analyzing {len(instances)} running instances")

        recommendations = []
        total_savings = 0.0

        for inst in instances:
            instance_id = inst["InstanceId"]
            instance_type = inst["InstanceType"]
            avg_cpu = self._get_avg_cpu(instance_id, days)

            if avg_cpu is not None and avg_cpu < cpu_threshold:
                recommended = DOWNSIZE_MAP.get(instance_type)
                if recommended:
                    current_cost = EC2_PRICING.get(instance_type, 0) * 730  # Monthly
                    new_cost = EC2_PRICING.get(recommended, 0) * 730
                    savings = current_cost - new_cost

                    recommendations.append({
                        "instance_id": instance_id,
                        "name": self._get_name_tag(inst),
                        "current_type": instance_type,
                        "recommended_type": recommended,
                        "avg_cpu_percent": round(avg_cpu, 1),
                        "current_monthly_cost": round(current_cost, 2),
                        "recommended_monthly_cost": round(new_cost, 2),
                        "monthly_savings": round(savings, 2),
                    })
                    total_savings += savings

        return {
            "instances_analyzed": len(instances),
            "recommendations": recommendations,
            "potential_savings": round(total_savings, 2),
            "cpu_threshold": cpu_threshold,
        }

    def _get_running_instances(self) -> list[dict]:
        """Get all running EC2 instances."""
        paginator = self.ec2.get_paginator("describe_instances")
        instances = []
        for page in paginator.paginate(Filters=[{"Name": "instance-state-name", "Values": ["running"]}]):
            for res in page["Reservations"]:
                instances.extend(res["Instances"])
        return instances

    def _get_avg_cpu(self, instance_id: str, days: int) -> float | None:
        """Get average CPU utilization over the period."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        try:
            response = self.cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start, EndTime=end,
                Period=3600, Statistics=["Average"],
            )
            points = response.get("Datapoints", [])
            if not points:
                return None
            return sum(p["Average"] for p in points) / len(points)
        except Exception as e:
            logger.warning(f"Failed to get CPU for {instance_id}: {e}")
            return None

    @staticmethod
    def _get_name_tag(instance: dict) -> str:
        """Extract Name tag from instance."""
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                return tag["Value"]
        return ""
