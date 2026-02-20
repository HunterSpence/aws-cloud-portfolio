# EventStream — Serverless Real-Time Analytics Pipeline

![AWS](https://img.shields.io/badge/AWS-Serverless-FF9900?logo=amazonaws)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![SAM](https://img.shields.io/badge/AWS_SAM-IaC-232F3E)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)

A production-grade serverless real-time analytics pipeline that ingests, processes, and aggregates streaming events using AWS managed services. Designed for high-throughput workloads with sub-second latency, automatic scaling, and built-in anomaly detection.

---

## Architecture

```
                         ┌─────────────────────────────────────────────────┐
                         │            EventStream Pipeline                 │
                         └─────────────────────────────────────────────────┘

  Clients                    Ingest                 Stream              Process
 ─────────            ──────────────────       ──────────────      ──────────────────
│  Web App │  HTTPS  │   API Gateway    │     │   Kinesis    │    │  Process Lambda  │
│  Mobile  │────────▶│  (REST + Auth)   │────▶│  Data Stream │───▶│  (Kinesis Trigger)│
│  IoT     │         │                  │     │  (2 shards)  │    │                  │
 ─────────            ──────────────────       ──────────────      ──────────────────
                              │                                     │           │
                              ▼                                     ▼           ▼
                      ──────────────────                    ─────────────  ───────────
                     │  Ingest Lambda   │                  │  S3 Data    ││ DynamoDB  │
                     │  (Validation +   │                  │  Lake       ││ (Real-time│
                     │   Enrichment)    │                  │  (Parquet)  ││  Metrics) │
                      ──────────────────                    ─────────────  ───────────
                                                                │
                         ──────────────────              ───────────────
                        │  Step Functions  │            │    Athena     │
                        │  (ETL Workflow)  │            │  (Ad-hoc SQL) │
                         ──────────────────              ───────────────
                                │
                      ──────────────────
                     │ Aggregate Lambda │───▶  SNS Alerts
                     │ (Hourly Rollups  │     (Anomaly Detection)
                     │  + Anomaly Det.) │
                      ──────────────────
```

---

## Features

- **Real-Time Ingestion** — API Gateway + Lambda validates and enriches events, writes to Kinesis
- **Stream Processing** — Kinesis-triggered Lambda transforms events to Parquet, stores in S3 data lake
- **Hourly Aggregation** — Step Functions orchestrates scheduled rollups with anomaly detection
- **Anomaly Detection** — Z-score based detection on event volumes and latency with SNS alerting
- **Data Lake** — Partitioned Parquet on S3, queryable via Athena (Hive-style partitioning)
- **Real-Time Metrics** — DynamoDB stores latest metrics for dashboards
- **Infrastructure as Code** — Full AWS SAM template with least-privilege IAM
- **Observability** — Structured JSON logging, CloudWatch metrics, X-Ray tracing

## Tech Stack

| Layer | Service | Purpose |
|-------|---------|---------|
| Ingestion | API Gateway + Lambda | Event validation, rate limiting |
| Streaming | Kinesis Data Streams | Durable ordered event stream |
| Processing | Lambda (Kinesis trigger) | Transform → Parquet → S3 |
| Storage | S3 + DynamoDB | Data lake + real-time metrics |
| Analytics | Athena | Ad-hoc SQL on Parquet |
| Orchestration | Step Functions | ETL workflow coordination |
| Alerting | SNS | Anomaly notifications |

---

## Deployment

### Prerequisites

- AWS CLI configured (`aws configure`)
- AWS SAM CLI (`pip install aws-sam-cli`)
- Python 3.12+
- S3 bucket for SAM artifacts

### Deploy

```bash
# Build
sam build

# Deploy (guided first time)
sam deploy --guided

# Subsequent deploys
sam deploy
```

### Test Locally

```bash
# Invoke ingest function
sam local invoke IngestFunction -e events/sample_event.json

# Start local API
sam local start-api

# Run unit tests
python -m pytest tests/ -v
```

---

## API Usage

### Ingest Event

```bash
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/events \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your-key>" \
  -d '{
    "event_type": "page_view",
    "source": "web",
    "user_id": "usr_12345",
    "properties": {
      "page": "/dashboard",
      "referrer": "https://google.com",
      "duration_ms": 2500
    }
  }'
```

### Query with Athena

```sql
SELECT event_type, COUNT(*) as count, AVG(latency_ms) as avg_latency
FROM eventstream.events
WHERE year = '2026' AND month = '02' AND day = '20'
GROUP BY event_type
ORDER BY count DESC;
```

---

## Cost Estimate (Monthly)

| Service | Config | Est. Cost |
|---------|--------|-----------|
| API Gateway | 1M requests | $3.50 |
| Lambda (3 functions) | 1M invocations, 256MB | $5.00 |
| Kinesis | 2 shards | $29.00 |
| S3 | 50GB storage | $1.15 |
| DynamoDB | On-demand, 1M writes | $1.25 |
| Athena | 10 queries/day, 100MB scanned | $0.50 |
| Step Functions | 1K executions | $0.03 |
| SNS | 1K notifications | $0.00 |
| **Total** | | **~$40/mo** |

> At low traffic, costs can be under $5/mo due to free tier eligibility.

---

## Project Structure

```
eventstream/
├── README.md
├── template.yaml              # SAM infrastructure
├── samconfig.toml             # Deployment config
├── src/
│   ├── ingest/handler.py      # Event validation + Kinesis write
│   ├── process/handler.py     # Stream processing → Parquet → S3
│   ├── aggregate/handler.py   # Hourly rollups + anomaly detection
│   └── common/
│       ├── models.py          # Pydantic event schemas
│       └── config.py          # Configuration management
├── athena/
│   ├── create_tables.sql      # Table definitions
│   └── sample_queries.sql     # Example analytics queries
├── step-functions/
│   └── etl-workflow.json      # Step Functions definition
├── tests/
│   ├── test_ingest.py
│   └── test_process.py
└── events/
    └── sample_event.json
```

---

## License

MIT
