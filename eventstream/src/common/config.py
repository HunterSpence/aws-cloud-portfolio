"""Configuration management for EventStream pipeline.

Loads settings from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Config:
    """Immutable pipeline configuration loaded from environment."""

    # General
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "dev"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    service_name: str = field(
        default_factory=lambda: os.getenv("POWERTOOLS_SERVICE_NAME", "eventstream")
    )

    # Kinesis
    kinesis_stream_name: str = field(
        default_factory=lambda: os.getenv("KINESIS_STREAM_NAME", "eventstream-dev")
    )

    # S3
    data_lake_bucket: str = field(
        default_factory=lambda: os.getenv("DATA_LAKE_BUCKET", "")
    )
    data_prefix: str = field(
        default_factory=lambda: os.getenv("DATA_PREFIX", "events/raw")
    )
    aggregation_prefix: str = field(
        default_factory=lambda: os.getenv("AGGREGATION_PREFIX", "events/aggregated")
    )

    # DynamoDB
    metrics_table: str = field(
        default_factory=lambda: os.getenv("METRICS_TABLE", "")
    )

    # SNS
    alert_topic_arn: str = field(
        default_factory=lambda: os.getenv("ALERT_TOPIC_ARN", "")
    )

    # Anomaly detection
    anomaly_z_threshold: float = field(
        default_factory=lambda: float(os.getenv("ANOMALY_Z_THRESHOLD", "3.0"))
    )
    anomaly_lookback_hours: int = field(
        default_factory=lambda: int(os.getenv("ANOMALY_LOOKBACK_HOURS", "168"))
    )

    # Processing
    max_batch_size: int = field(
        default_factory=lambda: int(os.getenv("MAX_BATCH_SIZE", "500"))
    )


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return singleton Config instance."""
    return Config()
