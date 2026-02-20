# CostPilot — Cloud Cost Optimization Engine

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Cost_Explorer-FF9900?logo=amazon-aws)
![CloudWatch](https://img.shields.io/badge/CloudWatch-Metrics-FF4F8B?logo=amazon-cloudwatch)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen)

**Automated AWS cost analysis, rightsizing recommendations, unused resource detection, and RI/Savings Plans optimization — with HTML/Markdown reporting and alerting.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CostPilot CLI                              │
│              analyze │ report │ watch │ unused                   │
└────────┬────────┬────────┬────────┬────────┬───────────────────┘
         │        │        │        │        │
    ┌────▼───┐┌───▼────┐┌──▼───┐┌──▼────┐┌──▼──────┐
    │Analyzer││RightSiz││Unused││Reserve.││ Alerts  │
    │        ││  er    ││Detect││ Advisor││         │
    └───┬────┘└───┬────┘└──┬───┘└──┬────┘└──┬──────┘
        │         │        │       │        │
   ┌────▼─────────▼────────▼───────▼────────▼──────┐
   │              AWS API Layer (boto3)              │
   ├────────┬──────────┬──────────┬────────────────┤
   │  Cost  │CloudWatch│   EC2    │   Budgets /    │
   │Explorer│ Metrics  │ELB/S3/  │  SES / Slack   │
   │        │          │EBS/EIP  │                 │
   └────────┴──────────┴──────────┴────────────────┘
                        │
              ┌─────────▼─────────┐
              │   Reporter Engine  │
              │  Jinja2 Templates  │
              │  HTML + Markdown   │
              └───────────────────┘
```

## Features

- **Cost Analysis** — 30/60/90-day spend breakdown by service, account, and region with trend detection and spike alerts
- **Rightsizing** — EC2 & RDS instance recommendations based on CloudWatch CPU/memory/network utilization
- **Unused Resource Detection** — Unattached EBS, idle ALBs, unassociated EIPs, empty S3 buckets, stopped EC2 >7 days, orphaned snapshots
- **RI & Savings Plans** — Utilization tracking, coverage analysis, purchase recommendations with break-even calculations
- **Reporting** — Dark-themed HTML and Markdown reports via Jinja2 templates
- **Alerting** — AWS Budgets integration, Slack webhooks, and SES email alerts
- **Cost Projections** — Linear regression forecasting for next-month spend

## Installation

```bash
git clone https://github.com/hunterspence/costpilot.git
cd costpilot
pip install -e .
```

## Configuration

```bash
# Set AWS credentials
export AWS_PROFILE=production

# Optional: Slack alerts
export COSTPILOT_SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Optional: SES alerts
export COSTPILOT_SES_SENDER=alerts@example.com
export COSTPILOT_SES_RECIPIENT=team@example.com
```

Or use a config file at `~/.costpilot/config.yaml`:

```yaml
aws_profile: production
alert_threshold_pct: 15
slack_webhook: https://hooks.slack.com/services/...
ses_sender: alerts@example.com
ses_recipients:
  - team@example.com
```

## Usage

```bash
# Full cost analysis (last 30 days)
costpilot analyze --days 30

# Generate HTML + Markdown reports
costpilot report --format html --output report.html
costpilot report --format markdown --output report.md

# Detect unused resources
costpilot unused --all
costpilot unused --ebs --eip --ec2

# Watch mode (continuous monitoring)
costpilot watch --interval 3600 --alert-threshold 15

# RI/Savings Plans analysis
costpilot analyze --include-reservations
```

## Sample Output

```
CostPilot Cost Analysis — 2026-02-01 to 2026-02-20
====================================================

Total Spend:        $14,832.47
Projected Month:    $22,248.71
Month-over-Month:   +8.3%

Top Services:
  1. Amazon EC2           $6,241.18  (42.1%)
  2. Amazon RDS           $3,108.54  (21.0%)
  3. Amazon S3            $1,927.33  (13.0%)

⚠ Spike Detected: EC2 spend +34% on Feb 14 ($892 vs $665 avg)

Rightsizing Opportunities:     12 instances    ~$1,840/mo savings
Unused Resources Found:         8 resources    ~$420/mo waste
RI Coverage Gap:               23%             ~$2,100/yr opportunity
```

See [sample-output/sample-report.md](sample-output/sample-report.md) for a full report.

## Project Structure

```
costpilot/
├── costpilot/
│   ├── __init__.py
│   ├── cli.py            # Click CLI interface
│   ├── analyzer.py       # Cost Explorer analysis
│   ├── rightsizer.py     # EC2/RDS rightsizing
│   ├── unused.py         # Unused resource detection
│   ├── reservations.py   # RI/Savings Plans advisor
│   ├── reporter.py       # Report generation
│   ├── alerts.py         # Alerting (Budgets/Slack/SES)
│   ├── models.py         # Data models
│   └── config.py         # Configuration
├── templates/
│   ├── report.html.j2
│   └── report.md.j2
├── tests/
├── sample-output/
├── setup.py
└── requirements.txt
```

## License

MIT
