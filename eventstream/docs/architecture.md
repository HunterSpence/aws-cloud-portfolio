# EventStream — Architecture & Data Flow

## Overview

EventStream is a **serverless real-time analytics pipeline** built on AWS. It ingests user-interaction events (page views, clicks, purchases, etc.), validates and enriches them, stores them in a queryable data lake, and computes near-real-time aggregations with anomaly detection.

## High-Level Architecture

```
Client → API Gateway → Ingest Lambda → Kinesis Data Stream
                                              │
                                              ▼
                                       Process Lambda
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                     ▼
                              S3 Data Lake          DynamoDB (hot)
                            (Parquet/JSON)         (recent metrics)
                                    │
                                    ▼
                         Step Functions ETL
                                    │
                                    ▼
                          Aggregate Lambda
                            │           │
                            ▼           ▼
                       DynamoDB     SNS Alerts
                     (aggregates)  (anomalies)
                                    
                         Athena ← S3 (ad-hoc queries)
```

## Component Details

### 1. Ingest Lambda (`src/ingest/handler.py`)

**Trigger:** API Gateway HTTP API (POST /events)

- Parses and validates incoming JSON against Pydantic schemas (`IngestEvent`)
- Rejects malformed or invalid events with 400 responses
- Enriches valid events: assigns `event_id`, normalizes timestamps, adds `ingested_at`
- Writes enriched events to **Kinesis Data Stream** for downstream processing
- Returns 200 with the assigned `event_id` to the caller

### 2. Process Lambda (`src/process/handler.py`)

**Trigger:** Kinesis Data Stream (batch of records)

- Reads batches of enriched events from Kinesis
- Derives Hive-style partition keys (`year/month/day/hour`) for the data lake
- Writes events as JSON to **S3** under a partitioned prefix structure:
  ```
  s3://bucket/events/year=2026/month=02/day=20/hour=14/batch-<uuid>.json
  ```
- Optionally writes hot-path metrics to **DynamoDB** for low-latency reads
- Reports batch item failures back to Kinesis for automatic retry

### 3. Aggregate Lambda (`src/aggregate/handler.py`)

**Trigger:** Step Functions (hourly schedule) or direct invocation

- Reads a time window of events from DynamoDB or S3
- Computes per-event-type metrics: total count, unique users, latency percentiles
- Runs a Z-score anomaly detection algorithm against historical baselines
- Writes `AggregationResult` records to **DynamoDB**
- Publishes `AnomalyAlert` to **SNS** when the Z-score exceeds the configured threshold

### 4. Step Functions ETL Workflow (`step-functions/etl-workflow.json`)

Orchestrates the aggregation pipeline on an hourly cadence:

1. **Determine window** — calculate the 1-hour window to aggregate
2. **Run Aggregate Lambda** — invoke with window parameters
3. **Check for anomalies** — branch on `anomaly_detected`
4. **Notify** — fan out SNS alerts if anomalies found
5. **Record completion** — write run metadata to DynamoDB

### 5. Athena Queries (`athena/`)

- `create_tables.sql` — defines the external table over the S3 data lake with Hive partitioning
- `sample_queries.sql` — example analytical queries (top events, user funnels, error rates)

### 6. Shared Layer (`src/common/`)

- `models.py` — Pydantic schemas: `IngestEvent`, `EnrichedEvent`, `AggregationResult`, `AnomalyAlert`
- `config.py` — Environment-based configuration (table names, bucket, stream, thresholds)

## Data Flow Summary

```
1.  Client POSTs event JSON to API Gateway
2.  Ingest Lambda validates → enriches → pushes to Kinesis
3.  Process Lambda reads Kinesis batch → partitions → writes S3 + DynamoDB
4.  Step Functions triggers Aggregate Lambda hourly
5.  Aggregate Lambda computes metrics → writes DynamoDB → alerts via SNS
6.  Analysts query the S3 data lake through Athena
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Kinesis over SQS** | Ordered, replayable stream; supports multiple consumers |
| **Pydantic validation** | Strict schema enforcement at the edge; clear error messages |
| **Hive-style partitioning** | Enables efficient Athena queries with partition pruning |
| **Z-score anomaly detection** | Simple, explainable, no ML infrastructure required |
| **Step Functions orchestration** | Visual workflow, built-in retry/error handling, audit trail |
| **SAM (not CDK)** | Template-level transparency; easier for portfolio reviewers to read |

## Infrastructure (SAM Template)

Defined in `template.yaml`. Key resources:

- **API Gateway** (HttpApi) — public endpoint with throttling
- **3 Lambda functions** — ingest, process, aggregate (Python 3.12, X-Ray tracing)
- **Kinesis Data Stream** — configurable shard count
- **S3 Bucket** — lifecycle policy for retention
- **DynamoDB Tables** — on-demand billing, TTL for hot data
- **SNS Topic** — anomaly alert fan-out
- **Step Functions State Machine** — ETL orchestration
- **IAM Roles** — least-privilege per function
