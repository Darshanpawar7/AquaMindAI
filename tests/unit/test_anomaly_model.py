"""Unit tests for backend/models/anomaly_model.py — Task 3.1."""
import sys
import os

import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.models import Reading
import backend.models.anomaly_model as am


def _reading(flow_rate: float, pressure: float, label: str = "normal") -> Reading:
    return Reading(
        pipe_id="p_test",
        timestamp="2024-01-01T00:00:00",
        flow_rate=flow_rate,
        pressure=pressure,
        anomaly_label=label,
    )


class TestPredict:
    def test_scores_in_range(self):
        """All returned scores must be in [0, 1]."""
        readings = [_reading(50.0, 60.0), _reading(95.0, 25.0, "leak")]
        scores = am.predict(readings)
        assert len(scores) == 2
        for s in scores:
            assert 0.0 <= s <= 1.0, f"Score {s} out of [0, 1]"

    def test_anomalous_scores_higher_than_normal(self):
        """Leak-pattern reading should score higher than a normal reading."""
        normal = _reading(50.0, 60.0, "normal")
        anomaly = _reading(95.0, 25.0, "leak")
        scores = am.predict([normal, anomaly])
        assert scores[1] > scores[0], (
            f"Expected anomaly score ({scores[1]:.4f}) > normal score ({scores[0]:.4f})"
        )

    def test_empty_input_returns_empty_list(self):
        """Empty input should return an empty list without error."""
        assert am.predict([]) == []

    def test_single_reading_returns_one_score(self):
        """Single reading should return exactly one score."""
        scores = am.predict([_reading(50.0, 60.0)])
        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    def test_output_length_matches_input(self):
        """Output list length must equal input list length."""
        readings = [_reading(50.0 + i, 60.0 - i) for i in range(10)]
        scores = am.predict(readings)
        assert len(scores) == len(readings)


class TestModelNotAvailableError:
    def test_raises_when_model_missing(self, monkeypatch):
        """ModelNotAvailableError is raised when _model_available is False."""
        monkeypatch.setattr(am, "_model_available", False)
        monkeypatch.setattr(am, "_model", None)
        with pytest.raises(am.ModelNotAvailableError):
            am.predict([_reading(50.0, 60.0)])

    def test_error_is_exception_subclass(self):
        """ModelNotAvailableError must be an Exception subclass."""
        assert issubclass(am.ModelNotAvailableError, Exception)


class TestLoadModel:
    def test_load_model_returns_model(self):
        """load_model() should return the fitted IsolationForest."""
        model = am.load_model()
        assert model is not None
        assert am._model_available is True
