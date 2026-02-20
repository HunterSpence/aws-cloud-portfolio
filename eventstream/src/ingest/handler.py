"""Ingest Lambda — validates incoming events and writes to Kinesis.

Receives API Gateway proxy events, validates the payload against
Pydantic schemas, enriches with metadata, and puts records onto
the Kinesis data stream for downstream processing.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from pydantic import ValidationError

# Add common layer to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))

from models import EnrichedEvent, IngestEvent  # noqa: E402
from config import get_config  # noqa: E402

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

kinesis = boto3.client("kinesis")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point for the ingest function.

    Args:
        event: API Gateway proxy event with JSON body.
        context: Lambda context object.

    Returns:
        API Gateway proxy response with status code and body.
    """
    config = get_config()
    request_id = event.get("requestContext", {}).get("requestId", str(uuid.uuid4()))

    logger.info("Ingest request received", extra={"request_id": request_id})

    try:
        body = _parse_body(event)
        validated = _validate_event(body)
        enriched = _enrich_event(validated)
        _put_to_kinesis(enriched, config.kinesis_stream_name)

        logger.info(
            "Event ingested successfully",
            extra={"event_id": enriched.event_id, "event_type": enriched.event_type},
        )

        return _response(200, {
            "message": "Event ingested",
            "event_id": enriched.event_id,
        })

    except ValidationError as exc:
        logger.warning("Validation failed", extra={"errors": exc.errors()})
        return _response(400, {
            "error": "Validation failed",
            "details": exc.errors(),
        })

    except json.JSONDecodeError:
        logger.warning("Invalid JSON body")
        return _response(400, {"error": "Invalid JSON body"})

    except Exception:
        logger.exception("Unexpected error during ingestion")
        return _response(500, {"error": "Internal server error"})


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    """Extract and parse the JSON body from the API Gateway event."""
    raw = event.get("body", "{}")
    if isinstance(raw, str):
        return json.loads(raw)
    return raw or {}


def _validate_event(body: dict[str, Any]) -> IngestEvent:
    """Validate the raw payload against the IngestEvent schema."""
    return IngestEvent(**body)


def _enrich_event(validated: IngestEvent) -> EnrichedEvent:
    """Create an enriched event with generated ID, timestamp, and partition keys."""
    now = datetime.now(timezone.utc)
    timestamp = (validated.timestamp or now).isoformat()

    enriched = EnrichedEvent(
        event_type=validated.event_type.value,
        source=validated.source.value,
        user_id=validated.user_id,
        properties=validated.properties,
        timestamp=timestamp,
        session_id=validated.session_id,
    )
    enriched.set_partition_keys()
    return enriched


def _put_to_kinesis(enriched: EnrichedEvent, stream_name: str) -> None:
    """Write the enriched event to Kinesis.

    Uses user_id as the partition key for consistent shard routing.
    """
    kinesis.put_record(
        StreamName=stream_name,
        Data=enriched.model_dump_json().encode("utf-8"),
        PartitionKey=enriched.user_id,
    )


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build an API Gateway proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }
