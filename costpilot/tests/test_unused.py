"""Unit tests for CostPilot unused resource detector."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from costpilot.unused import UnusedDetector


class TestUnusedDetector:
    """Tests for UnusedDetector."""

    def _make_detector(self, mock_config):
        return UnusedDetector(mock_config)

    def _setup_empty(self, mock_config):
        """Configure all clients to return empty results."""
        session = mock_config.get_session()
        ec2 = session.client("ec2")
        elb = session.client("elbv2")
        cw = session.client("cloudwatch")

        ec2.describe_volumes.return_value = {"Volumes": []}
        ec2.describe_addresses.return_value = {"Addresses": []}
        ec2.describe_instances.return_value = {"Reservations": []}
        ec2.describe_snapshots.return_value = {"Snapshots": []}
        elb.describe_load_balancers.return_value = {"LoadBalancers": []}
        return ec2, elb, cw

    def test_scan_empty_account(self, mock_config):
        self._setup_empty(mock_config)

        detector = self._make_detector(mock_config)
        result = detector.scan()

        assert result["total_unused"] == 0
        assert result["potential_savings"] == 0

    def test_unattached_ebs_detected(self, mock_config, sample_ebs_volumes):
        ec2, elb, cw = self._setup_empty(mock_config)
        ec2.describe_volumes.return_value = sample_ebs_volumes

        detector = self._make_detector(mock_config)
        result = detector.scan()

        ebs = result["resources"]["ebs_volumes"]
        assert len(ebs) == 2
        assert ebs[0]["id"] == "vol-0aaa111"
        assert ebs[0]["monthly_cost"] == 8.00  # 100GB * $0.08
        assert ebs[1]["monthly_cost"] == 4.00  # 50GB * $0.08

    def test_unassociated_eip_detected(self, mock_config, sample_addresses):
        ec2, elb, cw = self._setup_empty(mock_config)
        ec2.describe_addresses.return_value = sample_addresses

        detector = self._make_detector(mock_config)
        result = detector.scan()

        eips = result["resources"]["elastic_ips"]
        # Only the one without AssociationId
        assert len(eips) == 1
        assert eips[0]["id"] == "5.6.7.8"
        assert eips[0]["monthly_cost"] == 3.60

    def test_idle_load_balancer_detected(self, mock_config):
        ec2, elb, cw = self._setup_empty(mock_config)

        elb.describe_load_balancers.return_value = {
            "LoadBalancers": [
                {
                    "LoadBalancerName": "idle-alb",
                    "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123:loadbalancer/app/idle-alb/abc123",
                }
            ]
        }
        cw.get_metric_statistics.return_value = {"Datapoints": []}

        detector = self._make_detector(mock_config)
        result = detector.scan()

        lbs = result["resources"]["load_balancers"]
        assert len(lbs) == 1
        assert lbs[0]["id"] == "idle-alb"
        assert lbs[0]["monthly_cost"] == 16.20

    def test_active_load_balancer_not_flagged(self, mock_config):
        ec2, elb, cw = self._setup_empty(mock_config)

        elb.describe_load_balancers.return_value = {
            "LoadBalancers": [
                {
                    "LoadBalancerName": "busy-alb",
                    "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123:loadbalancer/app/busy-alb/def456",
                }
            ]
        }
        cw.get_metric_statistics.return_value = {
            "Datapoints": [{"Sum": 50000.0}]
        }

        detector = self._make_detector(mock_config)
        result = detector.scan()

        assert len(result["resources"]["load_balancers"]) == 0

    def test_stopped_instances_detected(self, mock_config):
        ec2, elb, cw = self._setup_empty(mock_config)

        ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-stopped1",
                            "InstanceType": "t3.medium",
                            "Tags": [{"Key": "Name", "Value": "old-dev"}],
                            "BlockDeviceMappings": [],
                        }
                    ]
                }
            ]
        }

        detector = self._make_detector(mock_config)
        result = detector.scan()

        stopped = result["resources"]["stopped_instances"]
        assert len(stopped) == 1
        assert stopped[0]["id"] == "i-stopped1"

    def test_old_snapshots_detected(self, mock_config):
        ec2, elb, cw = self._setup_empty(mock_config)

        ec2.describe_snapshots.return_value = {
            "Snapshots": [
                {
                    "SnapshotId": "snap-old1",
                    "VolumeSize": 200,
                    "StartTime": datetime(2025, 1, 1, tzinfo=timezone.utc),
                }
            ]
        }

        detector = self._make_detector(mock_config)
        result = detector.scan()

        snaps = result["resources"]["old_snapshots"]
        assert len(snaps) == 1
        assert snaps[0]["id"] == "snap-old1"
        assert snaps[0]["monthly_cost"] == 10.00  # 200GB * $0.05

    def test_total_savings_aggregated(self, mock_config, sample_ebs_volumes, sample_addresses):
        ec2, elb, cw = self._setup_empty(mock_config)
        ec2.describe_volumes.return_value = sample_ebs_volumes
        ec2.describe_addresses.return_value = sample_addresses

        detector = self._make_detector(mock_config)
        result = detector.scan()

        # EBS: 8+4=12, EIP: 3.60 → total 15.60
        assert result["potential_savings"] == 15.60
