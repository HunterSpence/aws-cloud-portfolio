"""CostPilot — Core Cost Analysis Engine.

Pulls AWS Cost Explorer data and generates spend analysis,
trend detection, and savings recommendations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from .config import Config

logger = logging.getLogger(__name__)


class CostAnalyzer:
    """Analyze AWS costs using Cost Explorer API."""

    def __init__(self, config: Config) -> None:
        self.session = config.get_session()
        self.ce = self.session.client("ce")

    def analyze(self, days: int = 30) -> dict[str, Any]:
        """Run full cost analysis for the specified period."""
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=days)

        logger.info(f"Analyzing costs from {start} to {end}")

        # Get daily costs by service
        daily = self._get_daily_costs(str(start), str(end))
        by_service = self._get_costs_by_service(str(start), str(end))
        by_region = self._get_costs_by_region(str(start), str(end))

        # Calculate metrics
        total_spend = sum(d["amount"] for d in daily)
        avg_daily = total_spend / max(len(daily), 1)
        projected_monthly = avg_daily * 30

        # Detect cost spikes (days > 2x average)
        spikes = [d for d in daily if d["amount"] > avg_daily * 2]

        # Top 5 services
        top_services = sorted(by_service, key=lambda x: x["amount"], reverse=True)[:5]

        return {
            "period": {"start": str(start), "end": str(end), "days": days},
            "total_spend": round(total_spend, 2),
            "avg_daily": round(avg_daily, 2),
            "projected_monthly": round(projected_monthly, 2),
            "daily_costs": daily,
            "by_service": by_service,
            "by_region": by_region,
            "top_services": top_services,
            "cost_spikes": spikes,
            "potential_savings": self._estimate_savings(by_service),
        }

    def _get_daily_costs(self, start: str, end: str) -> list[dict]:
        """Get daily cost breakdown."""
        response = self.ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
        )
        return [
            {
                "date": r["TimePeriod"]["Start"],
                "amount": float(r["Total"]["UnblendedCost"]["Amount"]),
            }
            for r in response["ResultsByTime"]
        ]

    def _get_costs_by_service(self, start: str, end: str) -> list[dict]:
        """Get costs grouped by AWS service."""
        response = self.ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        services = []
        for period in response["ResultsByTime"]:
            for group in period.get("Groups", []):
                services.append({
                    "service": group["Keys"][0],
                    "amount": float(group["Metrics"]["UnblendedCost"]["Amount"]),
                })
        # Merge duplicates across months
        merged: dict[str, float] = {}
        for s in services:
            merged[s["service"]] = merged.get(s["service"], 0) + s["amount"]
        return [{"service": k, "amount": round(v, 2)} for k, v in merged.items()]

    def _get_costs_by_region(self, start: str, end: str) -> list[dict]:
        """Get costs grouped by region."""
        response = self.ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
        )
        regions: dict[str, float] = {}
        for period in response["ResultsByTime"]:
            for group in period.get("Groups", []):
                region = group["Keys"][0]
                regions[region] = regions.get(region, 0) + float(group["Metrics"]["UnblendedCost"]["Amount"])
        return [{"region": k, "amount": round(v, 2)} for k, v in sorted(regions.items(), key=lambda x: -x[1])]

    def _estimate_savings(self, services: list[dict]) -> float:
        """Conservative savings estimate: 15-25% of top services via rightsizing + RIs."""
        total = sum(s["amount"] for s in services)
        return round(total * 0.20, 2)  # Conservative 20% estimate
