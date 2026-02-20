"""Data models for CostPilot analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    """Types of unused resources."""
    EBS_VOLUME = "ebs_volume"
    ELASTIC_IP = "elastic_ip"
    ALB = "alb"
    S3_BUCKET = "s3_bucket"
    EC2_INSTANCE = "ec2_instance"
    SNAPSHOT = "snapshot"


@dataclass
class ServiceCost:
    """Cost breakdown for a single AWS service."""
    service_name: str
    cost: float
    currency: str = "USD"
    percentage: float = 0.0
    change_pct: Optional[float] = None


@dataclass
class DailyCost:
    """Cost data for a single day."""
    date: date
    cost: float
    services: list[ServiceCost] = field(default_factory=list)


@dataclass
class CostSpike:
    """Detected cost anomaly."""
    date: date
    service: str
    actual_cost: float
    average_cost: float
    deviation_pct: float
    severity: Severity = Severity.MEDIUM


@dataclass
class CostAnalysis:
    """Complete cost analysis result."""
    start_date: date
    end_date: date
    total_cost: float
    projected_monthly: float
    mom_change_pct: float
    daily_costs: list[DailyCost] = field(default_factory=list)
    service_breakdown: list[ServiceCost] = field(default_factory=list)
    spikes: list[CostSpike] = field(default_factory=list)
    currency: str = "USD"


@dataclass
class RightsizeRecommendation:
    """EC2/RDS rightsizing recommendation."""
    resource_id: str
    resource_type: str
    region: str
    current_type: str
    recommended_type: str
    avg_cpu_pct: float
    max_cpu_pct: float
    avg_network_mbps: float
    current_monthly_cost: float
    projected_monthly_cost: float
    monthly_savings: float
    confidence: str = "high"


@dataclass
class UnusedResource:
    """Detected unused or idle resource."""
    resource_id: str
    resource_type: ResourceType
    region: str
    name: str = ""
    reason: str = ""
    monthly_cost: float = 0.0
    last_used: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ReservationAnalysis:
    """RI or Savings Plans analysis."""
    plan_type: str  # "RI" or "Savings Plan"
    utilization_pct: float
    coverage_pct: float
    total_commitment: float
    used_commitment: float
    wasted_spend: float
    recommendations: list[ReservationRecommendation] = field(default_factory=list)


@dataclass
class ReservationRecommendation:
    """Recommendation for RI or Savings Plan purchase."""
    service: str
    instance_family: str
    region: str
    term_months: int
    payment_option: str  # all_upfront, partial_upfront, no_upfront
    monthly_on_demand: float
    monthly_reserved: float
    monthly_savings: float
    break_even_months: float
    upfront_cost: float = 0.0


@dataclass
class CostReport:
    """Full cost optimization report."""
    generated_at: datetime
    analysis: Optional[CostAnalysis] = None
    rightsizing: list[RightsizeRecommendation] = field(default_factory=list)
    unused_resources: list[UnusedResource] = field(default_factory=list)
    reservations: Optional[ReservationAnalysis] = None
    total_potential_savings: float = 0.0

    def calculate_savings(self) -> float:
        """Calculate total potential monthly savings."""
        savings = sum(r.monthly_savings for r in self.rightsizing)
        savings += sum(u.monthly_cost for u in self.unused_resources)
        if self.reservations:
            savings += sum(r.monthly_savings for r in self.reservations.recommendations)
        self.total_potential_savings = savings
        return savings
