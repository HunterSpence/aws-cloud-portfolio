"""Unit tests for CostPilot cost analyzer."""

from unittest.mock import MagicMock, call

import pytest

from costpilot.analyzer import CostAnalyzer


class TestCostAnalyzer:
    """Tests for CostAnalyzer."""

    def _make_analyzer(self, mock_config):
        return CostAnalyzer(mock_config)

    def test_analyze_returns_expected_keys(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,  # daily
            sample_service_response,        # by service
            sample_region_response,          # by region
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        assert "total_spend" in result
        assert "avg_daily" in result
        assert "projected_monthly" in result
        assert "daily_costs" in result
        assert "by_service" in result
        assert "by_region" in result
        assert "top_services" in result
        assert "cost_spikes" in result
        assert "potential_savings" in result

    def test_total_spend_calculated(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,
            sample_service_response,
            sample_region_response,
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        # 12.50 + 8.00 + 45.00 = 65.50
        assert result["total_spend"] == 65.50

    def test_daily_costs_parsed(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,
            sample_service_response,
            sample_region_response,
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        assert len(result["daily_costs"]) == 3
        assert result["daily_costs"][0]["date"] == "2026-01-01"
        assert result["daily_costs"][0]["amount"] == 12.50

    def test_cost_spikes_detected(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,
            sample_service_response,
            sample_region_response,
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        # avg = 65.50/3 ≈ 21.83, spike threshold = 43.67 → 45.00 is a spike
        assert len(result["cost_spikes"]) == 1
        assert result["cost_spikes"][0]["amount"] == 45.00

    def test_top_services_sorted(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,
            sample_service_response,
            sample_region_response,
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        assert result["top_services"][0]["service"] == "Amazon EC2"
        assert result["top_services"][0]["amount"] == 100.00

    def test_savings_estimate(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,
            sample_service_response,
            sample_region_response,
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        # 20% of total services (100+25.50+80 = 205.50) → 41.10
        assert result["potential_savings"] == 41.10

    def test_by_region_returned(
        self, mock_config, sample_cost_explorer_response, sample_service_response, sample_region_response
    ):
        ce = mock_config.get_session().client("ce")
        ce.get_cost_and_usage.side_effect = [
            sample_cost_explorer_response,
            sample_service_response,
            sample_region_response,
        ]

        analyzer = self._make_analyzer(mock_config)
        result = analyzer.analyze(days=3)

        assert len(result["by_region"]) == 2
        assert result["by_region"][0]["region"] == "us-east-1"
