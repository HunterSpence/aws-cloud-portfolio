"""Unit tests for CostPilot rightsizer."""

from unittest.mock import MagicMock

import pytest

from costpilot.rightsizer import RightSizer, EC2_PRICING, DOWNSIZE_MAP


class TestRightSizer:
    """Tests for RightSizer."""

    def _make_sizer(self, mock_config):
        return RightSizer(mock_config)

    def test_recommends_downsize_for_low_cpu(
        self, mock_config, sample_ec2_instances, sample_cloudwatch_cpu_low
    ):
        session = mock_config.get_session()
        ec2 = session.client("ec2")
        cw = session.client("cloudwatch")

        # Paginator for describe_instances
        paginator = MagicMock()
        paginator.paginate.return_value = [sample_ec2_instances]
        ec2.get_paginator.return_value = paginator

        # Low CPU for both instances
        cw.get_metric_statistics.return_value = sample_cloudwatch_cpu_low

        sizer = self._make_sizer(mock_config)
        result = sizer.analyze(cpu_threshold=30.0, days=14)

        assert result["instances_analyzed"] == 2
        assert len(result["recommendations"]) == 2

        # Check first recommendation
        rec = next(r for r in result["recommendations"] if r["instance_id"] == "i-0abc123")
        assert rec["current_type"] == "t3.xlarge"
        assert rec["recommended_type"] == "t3.large"
        assert rec["monthly_savings"] > 0

    def test_no_recommendation_for_high_cpu(
        self, mock_config, sample_ec2_instances, sample_cloudwatch_cpu_high
    ):
        session = mock_config.get_session()
        ec2 = session.client("ec2")
        cw = session.client("cloudwatch")

        paginator = MagicMock()
        paginator.paginate.return_value = [sample_ec2_instances]
        ec2.get_paginator.return_value = paginator

        cw.get_metric_statistics.return_value = sample_cloudwatch_cpu_high

        sizer = self._make_sizer(mock_config)
        result = sizer.analyze(cpu_threshold=30.0, days=14)

        assert result["instances_analyzed"] == 2
        assert len(result["recommendations"]) == 0
        assert result["potential_savings"] == 0.0

    def test_no_instances(self, mock_config):
        session = mock_config.get_session()
        ec2 = session.client("ec2")

        paginator = MagicMock()
        paginator.paginate.return_value = [{"Reservations": []}]
        ec2.get_paginator.return_value = paginator

        sizer = self._make_sizer(mock_config)
        result = sizer.analyze()

        assert result["instances_analyzed"] == 0
        assert result["recommendations"] == []

    def test_no_cpu_data_skips_instance(self, mock_config, sample_ec2_instances):
        session = mock_config.get_session()
        ec2 = session.client("ec2")
        cw = session.client("cloudwatch")

        paginator = MagicMock()
        paginator.paginate.return_value = [sample_ec2_instances]
        ec2.get_paginator.return_value = paginator

        cw.get_metric_statistics.return_value = {"Datapoints": []}

        sizer = self._make_sizer(mock_config)
        result = sizer.analyze()

        assert result["recommendations"] == []

    def test_name_tag_extraction(self):
        instance = {"Tags": [{"Key": "Env", "Value": "prod"}, {"Key": "Name", "Value": "my-server"}]}
        assert RightSizer._get_name_tag(instance) == "my-server"

    def test_name_tag_missing(self):
        assert RightSizer._get_name_tag({"Tags": []}) == ""
        assert RightSizer._get_name_tag({}) == ""

    def test_savings_calculation(
        self, mock_config, sample_ec2_instances, sample_cloudwatch_cpu_low
    ):
        session = mock_config.get_session()
        ec2 = session.client("ec2")
        cw = session.client("cloudwatch")

        paginator = MagicMock()
        paginator.paginate.return_value = [sample_ec2_instances]
        ec2.get_paginator.return_value = paginator
        cw.get_metric_statistics.return_value = sample_cloudwatch_cpu_low

        sizer = self._make_sizer(mock_config)
        result = sizer.analyze(cpu_threshold=30.0)

        total = sum(r["monthly_savings"] for r in result["recommendations"])
        assert result["potential_savings"] == round(total, 2)
