# CostPilot Architecture

## Overview

CostPilot is a Python-based AWS cost optimization engine that analyzes cloud spending, identifies underutilized resources, and generates actionable savings recommendations.

## Data Flow

```
┌──────────────┐     ┌───────────────┐     ┌─────────────────┐
│  CLI / Entry  │────▶│   Analyzers   │────▶│ Report Generator│
│  (cli.py)     │     │               │     │  (reporter.py)  │
└──────────────┘     │ ┌───────────┐ │     └────────┬────────┘
                     │ │ analyzer  │ │              │
                     │ │ rightsizer│ │     ┌────────▼────────┐
                     │ │ unused    │ │     │  Jinja2 Templates│
                     │ │reservations│ │     │  (HTML / MD)    │
                     │ └───────────┘ │     └─────────────────┘
                     └───────┬───────┘
                             │
                     ┌───────▼───────┐
                     │   AWS APIs    │
                     │ (boto3 SDK)   │
                     └───────────────┘
```

## Modules

### `analyzer.py` — Cost Analysis Engine
- **API calls:** `ce:GetCostAndUsage` (3 calls per analysis)
  - Daily costs (DAILY granularity, UnblendedCost)
  - Costs grouped by SERVICE (MONTHLY granularity)
  - Costs grouped by REGION (MONTHLY granularity)
- **Logic:** Calculates total spend, daily average, projected monthly cost, detects cost spikes (>2× daily average), estimates 20% savings potential from top services
- **Output:** Dict with period, totals, breakdowns, spike list, savings estimate

### `rightsizer.py` — EC2 Rightsizing
- **API calls:**
  - `ec2:DescribeInstances` (paginated, filter: running)
  - `cloudwatch:GetMetricStatistics` (per instance — CPUUtilization, 1h period)
- **Logic:** For each running instance, fetches 14-day average CPU. If avg CPU < threshold (default 30%), looks up a downsize mapping and calculates monthly savings using approximate On-Demand pricing
- **Output:** List of recommendations with instance ID, current/recommended type, CPU stats, cost delta

### `unused.py` — Unused Resource Detector
- **API calls:**
  - `ec2:DescribeVolumes` (filter: status=available)
  - `ec2:DescribeAddresses` (all, check AssociationId)
  - `elbv2:DescribeLoadBalancers` + `cloudwatch:GetMetricStatistics` (RequestCount per ALB)
  - `ec2:DescribeInstances` (filter: state=stopped)
  - `ec2:DescribeSnapshots` (owner=self)
- **Logic:** Scans five resource categories for waste — unattached EBS, unused EIPs, idle ALBs (0 requests in 7 days), long-stopped EC2, old snapshots (>30 days)
- **Output:** Dict with per-category resource lists and aggregated savings

### `reporter.py` — Report Generation
- Consumes output dicts from all analyzers
- Renders Markdown report (inline) or HTML/Markdown via Jinja2 templates in `templates/`

### `config.py` — Configuration
- Loads settings from `~/.costpilot/config.yaml`, environment variables, and defaults
- Manages boto3 session creation with optional AWS profile

### `models.py` — Data Classes
- Typed dataclasses for all domain objects (CostAnalysis, RightsizeRecommendation, UnusedResource, etc.)
- Used for structured output and potential serialization

### `alerts.py` — Alerting
- Slack webhook and SES email notifications for cost anomalies

### `reservations.py` — RI & Savings Plans
- Analyzes Reserved Instance and Savings Plans utilization and coverage

## AWS Permissions Required

```json
{
  "Effect": "Allow",
  "Action": [
    "ce:GetCostAndUsage",
    "ec2:DescribeInstances",
    "ec2:DescribeVolumes",
    "ec2:DescribeAddresses",
    "ec2:DescribeSnapshots",
    "elasticloadbalancing:DescribeLoadBalancers",
    "cloudwatch:GetMetricStatistics"
  ],
  "Resource": "*"
}
```

## Testing Strategy

Tests use `unittest.mock` to mock all boto3 clients. No AWS credentials needed to run the test suite. Fixtures in `tests/conftest.py` provide realistic API response shapes.
