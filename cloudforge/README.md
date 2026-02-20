# ☁️ CloudForge — Multi-Region Infrastructure Framework

![Terraform](https://img.shields.io/badge/Terraform-≥1.6-7B42BC?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Multi--Region-FF9900?logo=amazonaws&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![IaC](https://img.shields.io/badge/IaC-Production--Ready-blue)

> A production-grade, multi-region AWS infrastructure framework built with Terraform modules.
> Designed for high availability, security, and operational excellence following AWS Well-Architected principles.

---

## 🏗️ Architecture

```
                          ┌─────────────────────────────────┐
                          │          Route 53 DNS           │
                          │     (Latency-based routing)     │
                          └────────────┬────────────────────┘
                                       │
                          ┌────────────▼────────────────────┐
                          │     CloudFront Distribution      │
                          │   ┌───────────────────────┐     │
                          │   │    AWS WAF (WebACL)    │     │
                          │   └───────────────────────┘     │
                          └────────────┬────────────────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               │  Region: us-east-1    │    Region: eu-west-1  │
               │                       │                       │
     ┌─────────▼─────────┐  ┌─────────▼─────────┐            │
     │    VPC 10.0.0.0/16 │  │  VPC 10.1.0.0/16  │            │
     │                     │  │                    │            │
     │  ┌──────────────┐  │  │  ┌──────────────┐ │            │
     │  │ Public Subnet │  │  │  │ Public Subnet│ │            │
     │  │  AZ-a,b,c     │  │  │  │  AZ-a,b,c   │ │            │
     │  │  ┌─────────┐  │  │  │  │  ┌────────┐ │ │            │
     │  │  │  ALB    │  │  │  │  │  │  ALB   │ │ │            │
     │  │  └────┬────┘  │  │  │  └───┬──────┘ │ │            │
     │  └───────┼───────┘  │  └──────┼────────┘ │            │
     │  ┌───────▼───────┐  │  ┌──────▼────────┐ │            │
     │  │Private Subnet │  │  │Private Subnet │ │            │
     │  │  AZ-a,b,c     │  │  │  AZ-a,b,c     │ │            │
     │  │               │  │  │               │ │            │
     │  │ ┌───────────┐ │  │  │ ┌───────────┐ │ │            │
     │  │ │ECS Fargate│ │  │  │ │ECS Fargate│ │ │            │
     │  │ │ Service   │ │  │  │ │ Service   │ │ │            │
     │  │ └─────┬─────┘ │  │  │ └─────┬─────┘ │ │            │
     │  └───────┼───────┘  │  └───────┼───────┘ │            │
     │  ┌───────▼───────┐  │  ┌───────▼───────┐ │            │
     │  │  DB Subnet    │  │  │  DB Subnet    │ │            │
     │  │ ┌───────────┐ │  │  │ ┌───────────┐ │ │            │
     │  │ │  Aurora    │ │  │  │ │  Aurora    │ │ │            │
     │  │ │ PostgreSQL│ │  │  │ │ Read Repl. │ │ │            │
     │  │ └───────────┘ │  │  │ └───────────┘ │ │            │
     │  └───────────────┘  │  └───────────────┘ │            │
     └─────────────────────┘  └─────────────────┘            │
               │                       │                      │
     ┌─────────▼───────────────────────▼──────────┐          │
     │          CloudWatch Monitoring              │          │
     │  Dashboards • Alarms • SNS • Log Groups    │          │
     └─────────────────────────────────────────────┘          │
```

---

## ✨ Features

| Category | Details |
|----------|---------|
| **Networking** | Multi-AZ VPC with public/private/database subnets, NAT Gateways, VPC Flow Logs |
| **Compute** | ECS Fargate with auto-scaling, health checks, blue/green ready |
| **Database** | Aurora PostgreSQL with read replicas, encryption at rest, automated backups |
| **CDN & Security** | CloudFront + WAF + ACM TLS certificates + Route 53 DNS |
| **Observability** | CloudWatch dashboards, metric alarms, SNS alerting, centralized log groups |
| **CI/CD** | GitHub Actions pipeline with lint → plan → apply workflow |
| **Multi-Region** | Primary + DR region with provider aliases |
| **Security** | KMS encryption, security groups, IAM least-privilege, VPC Flow Logs |

---

## 📋 Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.6
- [AWS CLI](https://aws.amazon.com/cli/) v2 configured with credentials
- An AWS account with permissions for VPC, ECS, RDS, CloudFront, Route 53, WAF, ACM, CloudWatch, SNS, KMS
- A registered domain in Route 53 (for CDN/DNS module)
- Docker (for building container images pushed to ECR)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/hunterspence/cloudforge.git
cd cloudforge

# 2. Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 3. Initialize Terraform
terraform init

# 4. Review the execution plan
terraform plan -out=tfplan

# 5. Apply the infrastructure
terraform apply tfplan
```

---

## 📁 Project Structure

```
cloudforge/
├── main.tf                    # Root module — orchestrates all child modules
├── variables.tf               # Input variables with defaults
├── outputs.tf                 # Stack outputs (ALB DNS, RDS endpoint, etc.)
├── providers.tf               # AWS provider with multi-region aliases
├── terraform.tfvars.example   # Example variable values
├── modules/
│   ├── vpc/                   # VPC, subnets, NAT, flow logs
│   ├── ecs/                   # Fargate cluster, ALB, auto-scaling, ECR
│   ├── database/              # Aurora PostgreSQL cluster
│   ├── cdn/                   # CloudFront, WAF, Route 53, ACM
│   └── monitoring/            # CloudWatch dashboards, alarms, SNS
└── ci-cd/
    └── github-actions.yml     # CI/CD pipeline
```

---

## 💰 Cost Estimate

| Resource | Monthly Estimate (us-east-1) |
|----------|------------------------------|
| NAT Gateway (3× AZ) | ~$97 + data |
| ALB | ~$22 + LCU |
| ECS Fargate (2× 0.5vCPU/1GB) | ~$29 |
| Aurora PostgreSQL (db.r6g.large) | ~$175 |
| CloudFront | ~$1 + requests |
| WAF WebACL | ~$6 + rules |
| CloudWatch | ~$3 |
| **Estimated Total** | **~$333/mo** |

> 💡 Use `terraform plan` to preview exact resource counts. Costs vary by usage.

---

## 🔧 Configuration

Key variables in `terraform.tfvars`:

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Prefix for all resource names | `cloudforge` |
| `environment` | Environment tag | `production` |
| `primary_region` | Primary AWS region | `us-east-1` |
| `dr_region` | Disaster recovery region | `eu-west-1` |
| `domain_name` | Your Route 53 domain | — |
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` |
| `db_instance_class` | Aurora instance size | `db.r6g.large` |

See [`variables.tf`](variables.tf) for the full list.

---

## 🧹 Teardown

```bash
# Destroy all resources (will prompt for confirmation)
terraform destroy

# Or auto-approve (use with caution)
terraform destroy -auto-approve
```

> ⚠️ This will delete **all** infrastructure including databases. Ensure backups are exported first.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built by <a href="https://github.com/hunterspence">Hunter Spence</a> · Cloud Solutions Architect
</p>
