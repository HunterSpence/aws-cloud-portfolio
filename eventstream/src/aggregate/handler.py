"""EventStream — Hourly Aggregation Lambda.

Aggregates metrics from DynamoDB, detects anomalies, and sends
SNS alerts when thresholds are exceeded.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

METRICS_TABLE = os.environ.get("METRICS_TABLE", "eventstream-metrics")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
ANOMALY_THRESHOLD = float(os.environ.get("ANOMALY_THRESHOLD", "2.0"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Run hourly aggregation and anomaly detection."""
    now = datetime.now(timezone.utc)
    current_hour = now.strftime("%H:00")
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(f"Running aggregation for {today} {current_hour}")

    table = dynamodb.Table(METRICS_TABLE)

    # Get today's metrics
    today_metrics = _query_metrics(table, today)
    yesterday_metrics = _query_metrics(table, yesterday)

    # Calculate totals
    today_total = sum(m.get("event_count", 0) for m in today_metrics)
    yesterday_total = sum(m.get("event_count", 0) for m in yesterday_metrics)

    # Anomaly detection: compare today vs yesterday
    anomalies = []
    if yesterday_total > 0:
        ratio = today_total / yesterday_total
        if ratio > ANOMALY_THRESHOLD:
            anomalies.append({
                "type": "volume_spike",
                "message": f"Event volume {ratio:.1f}x higher than yesterday ({today_total} vs {yesterday_total})",
                "severity": "HIGH" if ratio > 3.0 else "MEDIUM",
            })
        elif ratio < (1 / ANOMALY_THRESHOLD):
            anomalies.append({
                "type": "volume_drop",
                "message": f"Event volume {ratio:.1f}x lower than yesterday ({today_total} vs {yesterday_total})",
                "severity": "HIGH",
            })

    # Event type breakdown
    type_counts: dict[str, int] = {}
    for m in today_metrics:
        et = m.get("event_type", "unknown")
        type_counts[et] = type_counts.get(et, 0) + int(m.get("event_count", 0))

    # Write summary to DynamoDB
    summary = {
        "pk": f"SUMMARY#{today}",
        "sk": current_hour,
        "total_events": today_total,
        "event_types": type_counts,
        "anomalies": len(anomalies),
        "generated_at": now.isoformat(),
    }
    table.put_item(Item=summary)

    # Send alerts for anomalies
    if anomalies and SNS_TOPIC_ARN:
        _send_alert(anomalies, today_total, type_counts)

    return {
        "statusCode": 200,
        "body": {
            "date": today,
            "hour": current_hour,
            "total_events": today_total,
            "event_types": type_counts,
            "anomalies_detected": len(anomalies),
        },
    }


def _query_metrics(table: Any, date: str) -> list[dict]:
    """Query all metrics for a given date."""
    try:
        response = table.query(KeyConditionExpression=Key("pk").eq(f"METRICS#{date}"))
        return response.get("Items", [])
    except ClientError as e:
        logger.error(f"Failed to query metrics for {date}: {e}")
        return []


def _send_alert(anomalies: list[dict], total: int, types: dict) -> None:
    """Send anomaly alert via SNS."""
    message = {
        "subject": f"⚠️ EventStream Anomaly Alert — {len(anomalies)} issue(s)",
        "total_events_today": total,
        "event_breakdown": types,
        "anomalies": anomalies,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"EventStream Alert: {anomalies[0]['type']}",
            Message=json.dumps(message, indent=2, default=str),
        )
        logger.info(f"Alert sent for {len(anomalies)} anomalies")
    except ClientError as e:
        logger.error(f"Failed to send alert: {e}")
