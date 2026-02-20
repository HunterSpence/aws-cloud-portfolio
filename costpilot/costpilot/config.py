"""Configuration management for CostPilot."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".costpilot" / "config.yaml"


@dataclass
class CostPilotConfig:
    """Application configuration."""
    aws_profile: Optional[str] = None
    aws_region: str = "us-east-1"
    alert_threshold_pct: float = 15.0
    spike_std_devs: float = 2.0
    rightsizing_cpu_threshold: float = 40.0
    rightsizing_network_threshold_mbps: float = 5.0
    stopped_ec2_days: int = 7
    slack_webhook: Optional[str] = None
    ses_sender: Optional[str] = None
    ses_recipients: list[str] = field(default_factory=list)
    ses_region: str = "us-east-1"
    output_dir: str = "./reports"

    @classmethod
    def load(cls, path: Optional[str] = None) -> "CostPilotConfig":
        """Load config from YAML file, environment variables, and defaults.

        Priority: env vars > config file > defaults.
        """
        config = cls()

        # Load from file
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = yaml.safe_load(f) or {}
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                logger.info("Loaded config from %s", config_path)
            except Exception as e:
                logger.warning("Failed to load config from %s: %s", config_path, e)

        # Override with environment variables
        env_map = {
            "AWS_PROFILE": "aws_profile",
            "AWS_DEFAULT_REGION": "aws_region",
            "COSTPILOT_ALERT_THRESHOLD": "alert_threshold_pct",
            "COSTPILOT_SLACK_WEBHOOK": "slack_webhook",
            "COSTPILOT_SES_SENDER": "ses_sender",
            "COSTPILOT_SES_RECIPIENT": "ses_recipients",
        }
        for env_key, attr in env_map.items():
            val = os.environ.get(env_key)
            if val is not None:
                if attr == "alert_threshold_pct":
                    setattr(config, attr, float(val))
                elif attr == "ses_recipients":
                    config.ses_recipients = [v.strip() for v in val.split(",")]
                else:
                    setattr(config, attr, val)

        return config

    def save(self, path: Optional[str] = None) -> None:
        """Save current config to YAML file."""
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            k: v for k, v in self.__dict__.items()
            if v is not None and v != [] and v != ""
        }
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        logger.info("Saved config to %s", config_path)
