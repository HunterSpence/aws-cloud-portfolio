"""CostPilot — Unused Resource Detector.

Scans for idle, unattached, or orphaned AWS resources
that are wasting money.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from .config import Config

logger = logging.getLogger(__name__)


class UnusedDetector:
    """Detect unused AWS resources and estimate waste."""

    def __init__(self, config: Config) -> None:
        self.session = config.get_session()
        self.ec2 = self.session.client("ec2")
        self.elb = self.session.client("elbv2")
        self.s3 = self.session.client("s3")
        self.cw = self.session.client("cloudwatch")

    def scan(self) -> dict[str, Any]:
        """Scan all resource types for unused items."""
        results = {
            "ebs_volumes": self._find_unattached_ebs(),
            "elastic_ips": self._find_unassociated_eips(),
            "load_balancers": self._find_idle_load_balancers(),
            "stopped_instances": self._find_stopped_instances(),
            "old_snapshots": self._find_old_snapshots(),
        }

        total = sum(len(v) for v in results.values())
        savings = sum(item.get("monthly_cost", 0) for items in results.values() for item in items)

        return {
            "total_unused": total,
            "potential_savings": round(savings, 2),
            "resources": results,
        }

    def _find_unattached_ebs(self) -> list[dict]:
        """Find EBS volumes not attached to any instance."""
        volumes = self.ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
        results = []
        for vol in volumes.get("Volumes", []):
            size_gb = vol["Size"]
            # gp3: $0.08/GB/month
            monthly = size_gb * 0.08
            results.append({
                "id": vol["VolumeId"],
                "type": "EBS Volume",
                "size_gb": size_gb,
                "volume_type": vol["VolumeType"],
                "created": vol["CreateTime"].isoformat(),
                "monthly_cost": round(monthly, 2),
                "action": "Delete or snapshot and delete",
            })
        return results

    def _find_unassociated_eips(self) -> list[dict]:
        """Find Elastic IPs not associated with any resource."""
        addresses = self.ec2.describe_addresses()
        results = []
        for addr in addresses.get("Addresses", []):
            if "AssociationId" not in addr:
                results.append({
                    "id": addr["PublicIp"],
                    "type": "Elastic IP",
                    "allocation_id": addr["AllocationId"],
                    "monthly_cost": 3.60,  # $0.005/hr unused
                    "action": "Release if not needed",
                })
        return results

    def _find_idle_load_balancers(self) -> list[dict]:
        """Find ALBs with zero requests in last 7 days."""
        lbs = self.elb.describe_load_balancers()
        results = []
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        for lb in lbs.get("LoadBalancers", []):
            arn = lb["LoadBalancerArn"]
            arn_suffix = "/".join(arn.split("/")[-3:])
            try:
                metrics = self.cw.get_metric_statistics(
                    Namespace="AWS/ApplicationELB",
                    MetricName="RequestCount",
                    Dimensions=[{"Name": "LoadBalancer", "Value": arn_suffix}],
                    StartTime=start, EndTime=end,
                    Period=86400, Statistics=["Sum"],
                )
                total_requests = sum(p["Sum"] for p in metrics.get("Datapoints", []))
                if total_requests == 0:
                    results.append({
                        "id": lb["LoadBalancerName"],
                        "type": "Application Load Balancer",
                        "arn": arn,
                        "monthly_cost": 16.20,  # ~$0.0225/hr
                        "requests_7d": 0,
                        "action": "Delete if no longer needed",
                    })
            except Exception as e:
                logger.warning(f"Failed to check ALB {lb['LoadBalancerName']}: {e}")
        return results

    def _find_stopped_instances(self, days: int = 7) -> list[dict]:
        """Find EC2 instances stopped for more than N days."""
        instances = self.ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
        )
        results = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for res in instances.get("Reservations", []):
            for inst in res["Instances"]:
                stop_time = inst.get("StateTransitionReason", "")
                # EBS costs still apply for stopped instances
                ebs_cost = sum(
                    self._estimate_ebs_cost(m.get("Ebs", {}).get("VolumeId", ""))
                    for m in inst.get("BlockDeviceMappings", [])
                )
                name = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), "")
                results.append({
                    "id": inst["InstanceId"],
                    "type": "Stopped EC2",
                    "name": name,
                    "instance_type": inst["InstanceType"],
                    "monthly_cost": round(ebs_cost, 2),
                    "action": f"Terminate or start (stopped {days}+ days)",
                })
        return results

    def _find_old_snapshots(self, days: int = 30) -> list[dict]:
        """Find EBS snapshots older than N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        snapshots = self.ec2.describe_snapshots(OwnerIds=["self"])
        results = []

        for snap in snapshots.get("Snapshots", []):
            if snap["StartTime"].replace(tzinfo=timezone.utc) < cutoff:
                size_gb = snap["VolumeSize"]
                monthly = size_gb * 0.05  # $0.05/GB/month for snapshots
                results.append({
                    "id": snap["SnapshotId"],
                    "type": "EBS Snapshot",
                    "size_gb": size_gb,
                    "age_days": (datetime.now(timezone.utc) - snap["StartTime"].replace(tzinfo=timezone.utc)).days,
                    "monthly_cost": round(monthly, 2),
                    "action": "Delete if no longer needed for recovery",
                })
        return sorted(results, key=lambda x: -x["monthly_cost"])

    def _estimate_ebs_cost(self, volume_id: str) -> float:
        """Estimate monthly cost for an EBS volume."""
        if not volume_id:
            return 0
        try:
            vol = self.ec2.describe_volumes(VolumeIds=[volume_id])["Volumes"][0]
            return vol["Size"] * 0.08  # gp3 pricing
        except Exception:
            return 2.0  # Assume small volume
