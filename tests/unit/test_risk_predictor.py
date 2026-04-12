"""
Unit tests for the linear regression risk predictor.
"""

import pytest
from backend.models.risk_predictor import predict_failure_probability


class TestPredictFailureProbability:
    def test_all_features_present_returns_probability(self):
        result = predict_failure_probability(
            alert_frequency_7d=5.0,
            anomaly_severity_avg=0.5,
            pipe_age_years=25.0,
        )
        assert "failure_probability" in result
        assert "data_quality_warning" in result
        assert result["data_quality_warning"] is None

    def test_output_clamped_to_zero_one(self):
        # Extreme high values should clamp to 1.0
        result = predict_failure_probability(
            alert_frequency_7d=1000.0,
            anomaly_severity_avg=1.0,
            pipe_age_years=1000.0,
        )
        assert result["failure_probability"] == 1.0

        # Zero values should give 0.0
        result = predict_failure_probability(
            alert_frequency_7d=0.0,
            anomaly_severity_avg=0.0,
            pipe_age_years=0.0,
        )
        assert result["failure_probability"] == 0.0

    def test_known_values_formula(self):
        # alert_freq=10 -> norm=1.0, severity=0.5, pipe_age=50 -> norm=1.0
        # prob = 0.3*1.0 + 0.4*0.5 + 0.3*1.0 = 0.3 + 0.2 + 0.3 = 0.8
        result = predict_failure_probability(
            alert_frequency_7d=10.0,
            anomaly_severity_avg=0.5,
            pipe_age_years=50.0,
        )
        assert abs(result["failure_probability"] - 0.8) < 1e-9

    def test_alert_frequency_normalized_capped_at_1(self):
        # alert_freq=20 should be capped at 1.0 (same as 10)
        result_10 = predict_failure_probability(10.0, 0.5, 25.0)
        result_20 = predict_failure_probability(20.0, 0.5, 25.0)
        assert result_10["failure_probability"] == result_20["failure_probability"]

    def test_pipe_age_normalized_capped_at_1(self):
        # pipe_age=100 should be capped at 1.0 (same as 50)
        result_50 = predict_failure_probability(5.0, 0.5, 50.0)
        result_100 = predict_failure_probability(5.0, 0.5, 100.0)
        assert result_50["failure_probability"] == result_100["failure_probability"]

    def test_missing_alert_frequency_sets_warning(self):
        result = predict_failure_probability(
            alert_frequency_7d=None,
            anomaly_severity_avg=0.6,
            pipe_age_years=30.0,
        )
        assert result["data_quality_warning"] is not None
        assert "alert_frequency_7d" in result["data_quality_warning"]
        assert 0.0 <= result["failure_probability"] <= 1.0

    def test_missing_anomaly_severity_sets_warning(self):
        result = predict_failure_probability(
            alert_frequency_7d=5.0,
            anomaly_severity_avg=None,
            pipe_age_years=30.0,
        )
        assert result["data_quality_warning"] is not None
        assert "anomaly_severity_avg" in result["data_quality_warning"]
        assert 0.0 <= result["failure_probability"] <= 1.0

    def test_missing_pipe_age_sets_warning(self):
        result = predict_failure_probability(
            alert_frequency_7d=5.0,
            anomaly_severity_avg=0.6,
            pipe_age_years=None,
        )
        assert result["data_quality_warning"] is not None
        assert "pipe_age_years" in result["data_quality_warning"]
        assert 0.0 <= result["failure_probability"] <= 1.0

    def test_multiple_missing_features_listed_in_warning(self):
        result = predict_failure_probability(
            alert_frequency_7d=None,
            anomaly_severity_avg=None,
            pipe_age_years=30.0,
        )
        assert "alert_frequency_7d" in result["data_quality_warning"]
        assert "anomaly_severity_avg" in result["data_quality_warning"]

    def test_all_features_missing_returns_zero_probability_with_warning(self):
        result = predict_failure_probability(
            alert_frequency_7d=None,
            anomaly_severity_avg=None,
            pipe_age_years=None,
        )
        assert result["failure_probability"] == 0.0
        assert result["data_quality_warning"] is not None

    def test_probability_is_float(self):
        result = predict_failure_probability(5.0, 0.5, 25.0)
        assert isinstance(result["failure_probability"], float)

    def test_boundary_values(self):
        # Minimum boundary
        result = predict_failure_probability(0.0, 0.0, 0.0)
        assert result["failure_probability"] == 0.0

        # Maximum boundary (normalized)
        result = predict_failure_probability(10.0, 1.0, 50.0)
        assert result["failure_probability"] == 1.0
