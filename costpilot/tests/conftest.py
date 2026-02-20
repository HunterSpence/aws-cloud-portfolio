"""Shared pytest fixtures for CostPilot tests."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_config():
    """Create a mock Config object with a mock boto3 session."""
    config = MagicMock()
    session = MagicMock()
    config.get_session.return_value = session
    return config


@pytest.fixture
def mock_session(mock_config):
    """Return the mock boto3 session from the mock config."""
    return mock_config.get_session()


@pytest.fixture
def sample_cost_explorer_response():
    """Sample Cost Explorer get_cost_and_usage response (DAILY)."""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-01-01", "End": "2026-01-02"},
                "Total": {"UnblendedCost": {"Amount": "12.50", "Unit": "USD"}},
            },
            {
                "TimePeriod": {"Start": "2026-01-02", "End": "2026-01-03"},
                "Total": {"UnblendedCost": {"Amount": "8.00", "Unit": "USD"}},
            },
            {
                "TimePeriod": {"Start": "2026-01-03", "End": "2026-01-04"},
                "Total": {"UnblendedCost": {"Amount": "45.00", "Unit": "USD"}},
            },
        ]
    }


@pytest.fixture
def sample_service_response():
    """Sample Cost Explorer grouped-by-service response."""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-01-01", "End": "2026-02-01"},
                "Groups": [
                    {"Keys": ["Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "100.00"}}},
                    {"Keys": ["Amazon S3"], "Metrics": {"UnblendedCost": {"Amount": "25.50"}}},
                    {"Keys": ["Amazon RDS"], "Metrics": {"UnblendedCost": {"Amount": "80.00"}}},
                ],
            }
        ]
    }


@pytest.fixture
def sample_region_response():
    """Sample Cost Explorer grouped-by-region response."""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-01-01", "End": "2026-02-01"},
                "Groups": [
                    {"Keys": ["us-east-1"], "Metrics": {"UnblendedCost": {"Amount": "150.00"}}},
                    {"Keys": ["eu-west-1"], "Metrics": {"UnblendedCost": {"Amount": "55.50"}}},
                ],
            }
        ]
    }


@pytest.fixture
def sample_ec2_instances():
    """Sample EC2 describe_instances response for running instances."""
    return {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0abc123",
                        "InstanceType": "t3.xlarge",
                        "Tags": [{"Key": "Name", "Value": "web-server"}],
                    },
                    {
                        "InstanceId": "i-0def456",
                        "InstanceType": "m5.xlarge",
                        "Tags": [{"Key": "Name", "Value": "api-server"}],
                    },
                ]
            }
        ]
    }


@pytest.fixture
def sample_cloudwatch_cpu_low():
    """CloudWatch response with low CPU utilization."""
    return {
        "Datapoints": [
            {"Average": 5.2, "Timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc)},
            {"Average": 8.1, "Timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc)},
            {"Average": 3.9, "Timestamp": datetime(2026, 1, 3, tzinfo=timezone.utc)},
        ]
    }


@pytest.fixture
def sample_cloudwatch_cpu_high():
    """CloudWatch response with high CPU utilization."""
    return {
        "Datapoints": [
            {"Average": 72.0, "Timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc)},
            {"Average": 85.3, "Timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc)},
        ]
    }


@pytest.fixture
def sample_ebs_volumes():
    """Sample unattached EBS volumes."""
    return {
        "Volumes": [
            {
                "VolumeId": "vol-0aaa111",
                "Size": 100,
                "VolumeType": "gp3",
                "CreateTime": datetime(2025, 6, 1, tzinfo=timezone.utc),
            },
            {
                "VolumeId": "vol-0bbb222",
                "Size": 50,
                "VolumeType": "gp2",
                "CreateTime": datetime(2025, 9, 15, tzinfo=timezone.utc),
            },
        ]
    }


@pytest.fixture
def sample_addresses():
    """Sample Elastic IPs — one associated, one not."""
    return {
        "Addresses": [
            {"PublicIp": "1.2.3.4", "AllocationId": "eipalloc-aaa", "AssociationId": "eipassoc-111"},
            {"PublicIp": "5.6.7.8", "AllocationId": "eipalloc-bbb"},
        ]
    }
