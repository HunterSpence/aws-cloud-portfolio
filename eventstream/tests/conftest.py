"""Shared pytest fixtures for EventStream tests."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import boto3
import pytest
from moto import mock_aws


# Ensure Lambda handlers don't hit real AWS
@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    """Set dummy AWS credentials and config for every test."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", "eventstream-test")


@pytest.fixture
def sample_event() -> dict:
    """Return a minimal valid ingest event."""
    return {
        "event_type": "page_view",
        "source": "web",
        "user_id": "user-abc-123",
        "session_id": "sess-001",
        "properties": {"page": "/home", "referrer": "https://google.com"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def api_gateway_event(sample_event) -> dict:
    """Wrap sample_event in an API Gateway v2 proxy payload."""
    return {
        "version": "2.0",
        "routeKey": "POST /events",
        "rawPath": "/events",
        "body": json.dumps(sample_event),
        "isBase64Encoded": False,
        "requestContext": {
            "http": {"method": "POST", "path": "/events"},
            "requestId": "test-request-id",
        },
        "headers": {"content-type": "application/json"},
    }


@pytest.fixture
def kinesis_record(sample_event) -> dict:
    """Build a Kinesis event record wrapping sample_event."""
    import base64

    encoded = base64.b64encode(json.dumps(sample_event).encode()).decode()
    return {
        "Records": [
            {
                "kinesis": {
                    "data": encoded,
                    "sequenceNumber": "1",
                    "partitionKey": "user-abc-123",
                },
                "eventSource": "aws:kinesis",
                "eventSourceARN": "arn:aws:kinesis:us-east-1:123456789012:stream/test",
            }
        ]
    }


@pytest.fixture
def mock_aws_services():
    """Start moto mock for S3, DynamoDB, Kinesis, and SNS."""
    with mock_aws():
        region = "us-east-1"
        s3 = boto3.client("s3", region_name=region)
        s3.create_bucket(Bucket="test-events-bucket")

        dynamodb = boto3.resource("dynamodb", region_name=region)
        dynamodb.create_table(
            TableName="test-aggregations",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        kinesis = boto3.client("kinesis", region_name=region)
        kinesis.create_stream(StreamName="test-stream", ShardCount=1)

        sns = boto3.client("sns", region_name=region)
        topic = sns.create_topic(Name="test-alerts")

        yield {
            "s3": s3,
            "dynamodb": dynamodb,
            "kinesis": kinesis,
            "sns": sns,
            "topic_arn": topic["TopicArn"],
            "bucket": "test-events-bucket",
            "table": "test-aggregations",
            "stream": "test-stream",
        }
