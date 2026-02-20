# 🛡️ SentinelGuard — AWS Security & Compliance Baseline

[![Terraform](https://img.shields.io/badge/Terraform-1.6+-623CE4?logo=terraform)](https://terraform.io)
[![AWS](https://img.shields.io/badge/AWS-Security-FF9900?logo=amazonaws)](https://aws.amazon.com)
[![CIS](https://img.shields.io/badge/CIS-Benchmark_1.4-00599C)](https://cisecurity.org)
[![SOC2](https://img.shields.io/badge/SOC2-Type_II-2E86C1)](https://www.aicpa.org)
[![PCI-DSS](https://img.shields.io/badge/PCI--DSS-v4.0-E74C3C)](https://www.pcisecuritystandards.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Automated security baseline and continuous compliance for AWS organizations — CIS, SOC 2, and PCI-DSS controls enforced via Infrastructure as Code with real-time remediation.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AWS Organization                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SCP Guardrails                                │   │
│  │  • Block root access keys  • Enforce encryption  • Deny regions │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  CloudTrail   │  │  GuardDuty   │  │ AWS Config   │  │   IAM     │  │
│  │              │  │              │  │              │  │  Access   │  │
│  │ • Multi-region│  │ • Threat     │  │ • 15+ CIS    │  │  Analyzer │  │
│  │ • KMS encrypt│  │   intel      │  │   rules      │  │           │  │
│  │ • Log valid. │  │ • S3 protect │  │ • Auto-eval  │  │ • External│  │
│  │ • S3 + CW    │  │ • EKS protect│  │ • Remediate  │  │   access  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                 │                 │         │
│         └────────┬────────┴────────┬────────┘                 │         │
│                  ▼                 ▼                           │         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Security Hub                                 │   │
│  │  • CIS AWS Foundations v1.4    • AWS Foundational Best Practices│   │
│  │  • Aggregated findings         • Compliance scoring             │   │
│  └──────────────────────┬──────────────────────────────────────────┘   │
│                         │                                               │
│              ┌──────────▼──────────┐                                    │
│              │   EventBridge       │                                    │
│              │   (Finding Events)  │                                    │
│              └──┬──────┬───────┬───┘                                    │
│                 │      │       │                                        │
│      ┌──────────▼┐ ┌──▼─────┐ ┌▼──────────────┐                       │
│      │ Lambda:   │ │Lambda: │ │ Lambda:        │                       │
│      │ Auto-     │ │Alert   │ │ Compliance     │                       │
│      │ Remediate │ │Forward │ │ Reporter       │                       │
│      │           │ │        │ │                │                       │
│      │• Close S3 │ │• Slack │ │• PDF/HTML      │                       │
│      │• Revoke   │ │• Email │ │• S3 upload     │                       │
│      │  keys     │ │• PD    │ │• Executive     │                       │
│      │• Encrypt  │ │        │ │  summary       │                       │
│      │  EBS      │ │        │ │                │                       │
│      │• Block RDS│ │        │ │                │                       │
│      │• Quarant. │ │        │ │                │                       │
│      │  EC2      │ │        │ │                │                       │
│      └───────────┘ └────────┘ └────────────────┘                       │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              CloudWatch Security Dashboard                       │   │
│  │  • Finding trends  • Compliance %  • Remediation stats          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### Compliance Frameworks
| Framework | Controls | Coverage |
|-----------|----------|----------|
| **CIS AWS Foundations v1.4** | 15+ automated rules | IAM, logging, monitoring, networking |
| **SOC 2 Type II** | Trust service criteria | Security, availability, confidentiality |
| **PCI-DSS v4.0** | Requirement mapping | Encryption, access control, monitoring |

### Security Services
- **AWS Config** — 15+ managed rules with continuous evaluation and auto-remediation
- **GuardDuty** — Threat detection with S3 protection, EKS audit logs, and threat intel feeds
- **Security Hub** — Centralized findings aggregation with compliance scoring
- **CloudTrail** — Multi-region trail with KMS encryption and log file validation
- **IAM Access Analyzer** — Continuous monitoring of external resource access

### Automated Remediation
| Finding | Action | Lambda |
|---------|--------|--------|
| Public S3 bucket | Block public access | `auto-remediate` |
| Exposed IAM keys | Deactivate + notify | `auto-remediate` |
| Unencrypted EBS | Create encrypted snapshot | `auto-remediate` |
| Public RDS instance | Disable public access | `auto-remediate` |
| Compromised EC2 | Isolate via security group | `auto-remediate` |

### Organization Guardrails (SCPs)
- Deny disabling CloudTrail, GuardDuty, Config, or Security Hub
- Enforce S3 encryption and block public access
- Restrict to approved AWS regions
- Prevent root account access key creation
- Require IMDSv2 for EC2 instances

## Quick Start

### Prerequisites
- Terraform ≥ 1.6
- AWS CLI configured with admin credentials
- Python 3.11+ (for Lambda development)

### Deployment

```bash
git clone https://github.com/hunterspence/sentinelguard.git
cd sentinelguard

# Initialize
terraform init

# Review plan
terraform plan -var="environment=production" \
               -var="notification_email=security@company.com"

# Deploy
terraform apply -var="environment=production" \
                -var="notification_email=security@company.com"
```

### Configuration

```hcl
# terraform.tfvars
environment        = "production"
notification_email = "security@company.com"
slack_webhook_url  = "https://hooks.slack.com/services/..."
enable_guardduty   = true
enable_config      = true
enable_securityhub = true
approved_regions   = ["us-east-1", "us-west-2"]
```

## Project Structure

```
sentinelguard/
├── main.tf                          # Root orchestration
├── variables.tf                     # Input variables
├── outputs.tf                       # Stack outputs
├── modules/
│   ├── config-rules/                # AWS Config + 15 CIS rules
│   ├── guardduty/                   # GuardDuty threat detection
│   ├── securityhub/                 # Security Hub aggregation
│   ├── cloudtrail/                  # CloudTrail logging
│   └── iam-analyzer/               # IAM Access Analyzer
├── lambdas/
│   ├── auto-remediate/handler.py    # Auto-remediation engine
│   ├── alert-forwarder/handler.py   # Slack/email alerting
│   └── compliance-reporter/handler.py # Compliance reports
├── policies/
│   └── scp-guardrails.json          # Organization SCPs
└── dashboards/
    └── security-dashboard.json      # CloudWatch dashboard
```

## Cost Estimate

| Service | Monthly Cost (est.) |
|---------|-------------------|
| AWS Config (15 rules) | ~$30 |
| GuardDuty | ~$35 (varies by volume) |
| Security Hub | ~$15 |
| CloudTrail | ~$5 (S3 storage) |
| Lambda executions | ~$2 |
| **Total** | **~$87/month** |

## License

MIT — See [LICENSE](LICENSE) for details.

---

*Built by [Hunter Spence](https://github.com/hunterspence) as part of the AWS Cloud Architecture Portfolio.*
