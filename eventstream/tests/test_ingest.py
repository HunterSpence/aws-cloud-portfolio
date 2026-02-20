"""Tests for EventStream ingest Lambda."""
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def api_gateway_event():
    return {
        "httpMethod": "POST",
        "body": json.dumps({
            "event_type": "page_view",
            "source": "web-app",
            "user_id": "usr_123",
            "payload": {"page": "/home"}
        }),
        "headers": {"Content-Type": "application/json"}
    }


@patch("src.ingest.handler.kinesis")
def test_ingest_valid_event(mock_kinesis, api_gateway_event):
    mock_kinesis.put_record.return_value = {"ShardId": "shard-001", "SequenceNumber": "123"}
    
    from src.ingest.handler import handler
    response = handler(api_gateway_event, None)
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "accepted"
    assert "event_id" in body


def test_ingest_missing_body():
    event = {"httpMethod": "POST", "body": None}
    
    from src.ingest.handler import handler
    response = handler(event, None)
    
    assert response["statusCode"] == 400


def test_ingest_invalid_json():
    event = {"httpMethod": "POST", "body": "not-json{{{"}
    
    from src.ingest.handler import handler
    response = handler(event, None)
    
    assert response["statusCode"] == 400
