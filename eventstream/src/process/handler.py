"""EventStream — Kinesis Stream Processor Lambda.

Reads events from Kinesis, transforms data, writes to S3 (JSON lines)
and updates real-time metrics in DynamoDB.
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET_NAME = os.environ.get("DATA_LAKE_BUCKET", "eventstream-data-lake")
METRICS_TABLE = os.environ.get("METRICS_TABLE", "eventstream-metrics")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Process Kinesis records, write to S3 data lake and DynamoDB metrics."""
    records = event.get("Records", [])
    logger.info(f"Processing {len(records)} Kinesis records")

    processed = 0
    failed = 0
    batch: list[dict] = []
    metrics: dict[str, int] = {}

    for record in records:
        try:
            payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
            data = json.loads(payload)

            # Enrich with processing metadata
            data["processed_at"] = datetime.now(timezone.utc).isoformat()
            data["shard_id"] = record["kinesis"].get("partitionKey", "unknown")

            batch.append(data)

            # Aggregate metrics by event type
            event_type = data.get("event_type", "unknown")
            metrics[event_type] = metrics.get(event_type, 0) + 1

            processed += 1
        except Exception as e:
            logger.error(f"Failed to process record: {e}")
            failed += 1

    # Write batch to S3
    if batch:
        _write_to_s3(batch)

    # Update DynamoDB metrics
    if metrics:
        _update_metrics(metrics)

    result = {
        "statusCode": 200,
        "body": {
            "processed": processed,
            "failed": failed,
            "event_types": metrics,
        },
    }
    logger.info(f"Processing complete: {result['body']}")
    return result


def _write_to_s3(records: list[dict]) -> None:
    """Write records to S3 as JSON lines, partitioned by date/hour."""
    now = datetime.now(timezone.utc)
    key = (
        f"raw/year={now.year}/month={now.month:02d}/"
        f"day={now.day:02d}/hour={now.hour:02d}/"
        f"events-{now.strftime('%Y%m%d%H%M%S')}-{id(records)}.jsonl"
    )

    body = "\n".join(json.dumps(r, default=str) for r in records)

    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/x-ndjson",
            ServerSideEncryption="AES256",
        )
        logger.info(f"Wrote {len(records)} records to s3://{BUCKET_NAME}/{key}")
    except ClientError as e:
        logger.error(f"S3 write failed: {e}")
        raise


def _update_metrics(metrics: dict[str, int]) -> None:
    """Update real-time event counts in DynamoDB."""
    table = dynamodb.Table(METRICS_TABLE)
    now = datetime.now(timezone.utc)
    date_key = now.strftime("%Y-%m-%d")
    hour_key = now.strftime("%H:00")

    for event_type, count in metrics.items():
        try:
            table.update_item(
                Key={"pk": f"METRICS#{date_key}", "sk": f"{hour_key}#{event_type}"},
                UpdateExpression="ADD event_count :c SET updated_at = :t, event_type = :e",
                ExpressionAttributeValues={
                    ":c": count,
                    ":t": now.isoformat(),
                    ":e": event_type,
                },
            )
        except ClientError as e:
            logger.error(f"DynamoDB update failed for {event_type}: {e}")
