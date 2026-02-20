"""Pydantic event schemas for the EventStream pipeline.

Defines validation models for incoming events, processed records,
and aggregation results.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Supported event types."""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    PURCHASE = "purchase"
    SIGN_UP = "sign_up"
    LOGIN = "login"
    ERROR = "error"
    CUSTOM = "custom"


class EventSource(str, Enum):
    """Event source platforms."""
    WEB = "web"
    MOBILE_IOS = "mobile_ios"
    MOBILE_ANDROID = "mobile_android"
    API = "api"
    IOT = "iot"


class IngestEvent(BaseModel):
    """Schema for incoming raw events from API Gateway."""

    event_type: EventType
    source: EventSource
    user_id: str = Field(..., min_length=1, max_length=128)
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None
    session_id: str | None = None

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Ensure user_id contains no control characters."""
        if any(ord(c) < 32 for c in v):
            raise ValueError("user_id must not contain control characters")
        return v.strip()


class EnrichedEvent(BaseModel):
    """Event after validation and enrichment by the ingest Lambda."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    source: str
    user_id: str
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    session_id: str | None = None
    ingested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    year: str = ""
    month: str = ""
    day: str = ""
    hour: str = ""

    def set_partition_keys(self) -> None:
        """Derive Hive-style partition keys from timestamp."""
        dt = datetime.fromisoformat(self.timestamp)
        self.year = str(dt.year)
        self.month = f"{dt.month:02d}"
        self.day = f"{dt.day:02d}"
        self.hour = f"{dt.hour:02d}"


class AggregationResult(BaseModel):
    """Result of hourly aggregation."""

    window_start: str
    window_end: str
    event_type: str
    total_count: int = 0
    unique_users: int = 0
    avg_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    anomaly_detected: bool = False
    anomaly_score: float = 0.0


class AnomalyAlert(BaseModel):
    """Alert payload for SNS when anomaly is detected."""

    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str
    event_type: str
    current_value: float
    expected_value: float
    z_score: float
    window_start: str
    window_end: str
    severity: str = "WARNING"
    message: str = ""
