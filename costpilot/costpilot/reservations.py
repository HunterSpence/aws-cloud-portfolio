"""CostPilot — Reserved Instance & Savings Plans Analyzer."""

import logging
from typing import Any
import boto3
from .config import Config

logger = logging.getLogger(__name__)


class ReservationAnalyzer:
    """Analyze RI and Savings Plans utilization and coverage."""

    def __init__(self, config: Config) -> None:
        self.session = config.get_session()
        self.ce = self.session.client("ce")

    def analyze(self) -> dict[str, Any]:
        """Full RI/SP analysis with recommendations."""
        ri_utilization = self._get_ri_utilization()
        ri_coverage = self._get_ri_coverage()
        sp_utilization = self._get_sp_utilization()
        recommendations = self._get_recommendations()

        return {
            "reserved_instances": {
                "utilization_percent": ri_utilization,
                "coverage_percent": ri_coverage,
            },
            "savings_plans": {
                "utilization_percent": sp_utilization,
            },
            "recommendations": recommendations,
        }

    def _get_ri_utilization(self) -> float:
        """Get RI utilization percentage."""
        try:
            from datetime import datetime, timedelta, timezone
            end = datetime.now(timezone.utc).date()
            start = end - timedelta(days=30)
            resp = self.ce.get_reservation_utilization(
                TimePeriod={"Start": str(start), "End": str(end)},
            )
            total = resp.get("Total", {})
            return float(total.get("UtilizationPercentage", 0))
        except Exception as e:
            logger.warning(f"RI utilization query failed: {e}")
            return 0.0

    def _get_ri_coverage(self) -> float:
        """Get RI coverage percentage."""
        try:
            from datetime import datetime, timedelta, timezone
            end = datetime.now(timezone.utc).date()
            start = end - timedelta(days=30)
            resp = self.ce.get_reservation_coverage(
                TimePeriod={"Start": str(start), "End": str(end)},
            )
            total = resp.get("Total", {}).get("CoverageHours", {})
            return float(total.get("CoverageHoursPercentage", 0))
        except Exception as e:
            logger.warning(f"RI coverage query failed: {e}")
            return 0.0

    def _get_sp_utilization(self) -> float:
        """Get Savings Plans utilization."""
        try:
            from datetime import datetime, timedelta, timezone
            end = datetime.now(timezone.utc).date()
            start = end - timedelta(days=30)
            resp = self.ce.get_savings_plans_utilization(
                TimePeriod={"Start": str(start), "End": str(end)},
            )
            total = resp.get("Total", {})
            return float(total.get("Utilization", {}).get("UtilizationPercentage", 0))
        except Exception as e:
            logger.warning(f"SP utilization query failed: {e}")
            return 0.0

    def _get_recommendations(self) -> list[dict]:
        """Get RI purchase recommendations from Cost Explorer."""
        try:
            resp = self.ce.get_reservation_purchase_recommendation(
                Service="Amazon Elastic Compute Cloud - Compute",
                TermInYears="ONE_YEAR",
                PaymentOption="NO_UPFRONT",
                LookbackPeriodInDays="THIRTY_DAYS",
            )
            recs = []
            for rec in resp.get("Recommendations", []):
                for detail in rec.get("RecommendationDetails", []):
                    savings = float(detail.get("EstimatedMonthlySavingsAmount", 0))
                    if savings > 0:
                        recs.append({
                            "instance_type": detail.get("InstanceDetails", {}).get("EC2InstanceDetails", {}).get("InstanceType", "unknown"),
                            "recommended_count": int(detail.get("RecommendedNumberOfInstancesToPurchase", 0)),
                            "monthly_savings": round(savings, 2),
                            "upfront_cost": float(detail.get("UpfrontCost", 0)),
                            "break_even_months": round(float(detail.get("UpfrontCost", 0)) / max(savings, 0.01), 1),
                        })
            return sorted(recs, key=lambda x: -x["monthly_savings"])
        except Exception as e:
            logger.warning(f"RI recommendations failed: {e}")
            return []
