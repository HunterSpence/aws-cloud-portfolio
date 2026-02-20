"""Tests for EventStream process Lambda."""
import base64
import json
import pytest
from unittest.mock import patch, MagicMock


def _kinesis_record(data: dict) -> dict:
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    return {
        "kinesis": {
            "data": encoded,
            "partitionKey": "test-partition"
        }
    }


@patch("src.process.handler.dynamodb")
@patch("src.process.handler.s3")
def test_process_valid_records(mock_s3, mock_dynamodb):
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        "Records": [
            _kinesis_record({"event_type": "click", "user_id": "usr_1"}),
            _kinesis_record({"event_type": "page_view", "user_id": "usr_2"}),
        ]
    }
    
    from src.process.handler import handler
    result = handler(event, None)
    
    assert result["statusCode"] == 200
    assert result["body"]["processed"] == 2
    assert result["body"]["failed"] == 0
    mock_s3.put_object.assert_called_once()


@patch("src.process.handler.dynamodb")
@patch("src.process.handler.s3")
def test_process_handles_invalid_record(mock_s3, mock_dynamodb):
    event = {
        "Records": [
            {"kinesis": {"data": "not-valid-base64!!!"}},
            _kinesis_record({"event_type": "click"}),
        ]
    }
    
    from src.process.handler import handler
    result = handler(event, None)
    
    assert result["body"]["failed"] >= 1
