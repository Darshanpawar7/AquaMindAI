"""Unit tests for backend/detector/handler.py — Task 10.4."""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.models import Reading
from backend.models.anomaly_model import ModelNotAvailableError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_reading(pipe_id="pipe_001", timestamp="2024-01-01T00:00:00",
                  flow_rate=50.0, pressure=60.0, label="normal"):
    return Reading(
        pipe_id=pipe_id,
        timestamp=timestamp,
        flow_rate=flow_rate,
        pressure=pressure,
        anomaly_label=label,
        processed=False,
    )


def _make_raw_item(pipe_id="pipe_001", timestamp="2024-01-01T00:00:00",
                   flow_rate=50.0, pressure=60.0, label="normal"):
    return {
        "pipe_id": pipe_id,
        "timestamp": timestamp,
        "flow_rate": str(flow_rate),
        "pressure": str(pressure),
        "anomaly_label": label,
        "processed": False,
    }


# ---------------------------------------------------------------------------
# Test: batch processing — anomalous readings create alerts, normal ones don't
# ---------------------------------------------------------------------------

class TestBatchProcessing:
    def test_anomalous_readings_create_alerts_normal_do_not(self):
        """Readings with score > 0.5 create alerts; others don't."""
        readings = [
            _make_reading("pipe_001", "2024-01-01T00:00:00", 50.0, 60.0, "normal"),
            _make_reading("pipe_002", "2024-01-01T00:01:00", 95.0, 25.0, "leak"),
            _make_reading("pipe_003", "2024-01-01T00:02:00", 48.0, 58.0, "normal"),
        ]
        raw_items = [
            _make_raw_item("pipe_001", "2024-01-01T00:00:00", 50.0, 60.0, "normal"),
            _make_raw_item("pipe_002", "2024-01-01T00:01:00", 95.0, 25.0, "leak"),
            _make_raw_item("pipe_003", "2024-01-01T00:02:00", 48.0, 58.0, "normal"),
        ]
        # Scores: normal=0.1, anomalous=0.9, normal=0.2
        mock_scores = [0.1, 0.9, 0.2]

        mock_readings_table = MagicMock()
        mock_alerts_table = MagicMock()

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=(readings, raw_items)), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=mock_scores), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry") as mock_put, \
             patch("backend.detector.handler.boto3.resource") as mock_boto3:

            mock_boto3.return_value.Table.side_effect = [mock_readings_table, mock_alerts_table]

            from backend.detector.handler import handler
            result = handler({}, None)

        assert result["processed"] == 3
        assert result["alerts_created"] == 1
        assert mock_put.call_count == 1

    def test_all_normal_readings_create_no_alerts(self):
        """All normal readings (score <= 0.5) produce zero alerts."""
        readings = [_make_reading(f"pipe_{i:03d}", f"2024-01-01T00:0{i}:00") for i in range(5)]
        raw_items = [_make_raw_item(f"pipe_{i:03d}", f"2024-01-01T00:0{i}:00") for i in range(5)]
        mock_scores = [0.1, 0.2, 0.3, 0.4, 0.5]

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=(readings, raw_items)), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=mock_scores), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry") as mock_put, \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            result = handler({}, None)

        assert result["processed"] == 5
        assert result["alerts_created"] == 0
        assert mock_put.call_count == 0

    def test_all_anomalous_readings_create_alerts(self):
        """All anomalous readings (score > 0.5) each produce an alert."""
        readings = [_make_reading(f"pipe_{i:03d}", f"2024-01-01T00:0{i}:00", 90.0, 20.0, "leak")
                    for i in range(3)]
        raw_items = [_make_raw_item(f"pipe_{i:03d}", f"2024-01-01T00:0{i}:00", 90.0, 20.0, "leak")
                     for i in range(3)]
        mock_scores = [0.8, 0.9, 0.7]

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=(readings, raw_items)), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=mock_scores), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry") as mock_put, \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            result = handler({}, None)

        assert result["processed"] == 3
        assert result["alerts_created"] == 3
        assert mock_put.call_count == 3


# ---------------------------------------------------------------------------
# Test: handler returns correct summary counts
# ---------------------------------------------------------------------------

class TestHandlerSummary:
    def test_empty_readings_returns_zero_counts(self):
        """No unprocessed readings → processed=0, alerts_created=0."""
        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=([], [])), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            result = handler({}, None)

        assert result == {"processed": 0, "alerts_created": 0}

    def test_summary_counts_match_actual_processing(self):
        """Summary counts accurately reflect processed and alert counts."""
        readings = [
            _make_reading("pipe_001", "2024-01-01T00:00:00", 90.0, 20.0, "leak"),
            _make_reading("pipe_002", "2024-01-01T00:01:00", 50.0, 60.0, "normal"),
            _make_reading("pipe_003", "2024-01-01T00:02:00", 88.0, 22.0, "degradation"),
        ]
        raw_items = [
            _make_raw_item("pipe_001", "2024-01-01T00:00:00", 90.0, 20.0, "leak"),
            _make_raw_item("pipe_002", "2024-01-01T00:01:00", 50.0, 60.0, "normal"),
            _make_raw_item("pipe_003", "2024-01-01T00:02:00", 88.0, 22.0, "degradation"),
        ]
        mock_scores = [0.85, 0.15, 0.75]

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=(readings, raw_items)), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=mock_scores), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry"), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            result = handler({}, None)

        assert result["processed"] == 3
        assert result["alerts_created"] == 2


# ---------------------------------------------------------------------------
# Test: 503 behavior when model unavailable
# ---------------------------------------------------------------------------

class TestModelUnavailable:
    def test_raises_runtime_error_when_model_unavailable(self):
        """RuntimeError is raised when ModelNotAvailableError occurs."""
        readings = [_make_reading()]
        raw_items = [_make_raw_item()]

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=(readings, raw_items)), \
             patch("backend.detector.handler.anomaly_model.predict",
                   side_effect=ModelNotAvailableError("model file missing")), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            with pytest.raises(RuntimeError, match="Model not available"):
                handler({}, None)

    def test_model_unavailable_error_message_contains_cause(self):
        """RuntimeError message includes the original ModelNotAvailableError text."""
        readings = [_make_reading()]
        raw_items = [_make_raw_item()]

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=(readings, raw_items)), \
             patch("backend.detector.handler.anomaly_model.predict",
                   side_effect=ModelNotAvailableError("isolation_forest.pkl not found")), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            with pytest.raises(RuntimeError) as exc_info:
                handler({}, None)

        assert "Model not available" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test: detector writes correct Alert fields
# ---------------------------------------------------------------------------

class TestAlertFields:
    def test_alert_contains_required_fields(self):
        """Written alert item must contain pipe_id, timestamp, anomaly_type, flow_rate, pressure."""
        reading = _make_reading("pipe_007", "2024-06-15T12:00:00", 92.0, 18.0, "leak")
        raw_item = _make_raw_item("pipe_007", "2024-06-15T12:00:00", 92.0, 18.0, "leak")

        captured_items = []

        def capture_put(table, item):
            captured_items.append(item)

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=([reading], [raw_item])), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=[0.9]), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry", side_effect=capture_put), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            handler({}, None)

        assert len(captured_items) == 1
        item = captured_items[0]
        assert item["pipe_id"] == "pipe_007"
        assert item["timestamp"] == "2024-06-15T12:00:00"
        assert item["anomaly_type"] == "leak"
        assert float(item["flow_rate"]) == 92.0
        assert float(item["pressure"]) == 18.0

    def test_alert_contains_all_required_fields(self):
        """Written alert must contain all Alert schema fields including TTL."""
        reading = _make_reading("pipe_010", "2024-06-15T13:00:00", 88.0, 22.0, "degradation")
        raw_item = _make_raw_item("pipe_010", "2024-06-15T13:00:00", 88.0, 22.0, "degradation")

        captured_items = []

        def capture_put(table, item):
            captured_items.append(item)

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=([reading], [raw_item])), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=[0.8]), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry", side_effect=capture_put), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            handler({}, None)

        assert len(captured_items) == 1
        item = captured_items[0]
        required_fields = {
            "alert_id", "pipe_id", "timestamp", "anomaly_type",
            "anomaly_score", "failure_probability", "priority_score",
            "priority_level", "immediate_action_required",
            "flow_rate", "pressure", "ttl",
        }
        for field in required_fields:
            assert field in item, f"Missing field: {field}"

    def test_normal_label_maps_to_noise_anomaly_type(self):
        """Readings with anomaly_label='normal' but high score get anomaly_type='noise'."""
        reading = _make_reading("pipe_011", "2024-06-15T14:00:00", 85.0, 25.0, "normal")
        raw_item = _make_raw_item("pipe_011", "2024-06-15T14:00:00", 85.0, 25.0, "normal")

        captured_items = []

        def capture_put(table, item):
            captured_items.append(item)

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=([reading], [raw_item])), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=[0.75]), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry", side_effect=capture_put), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            handler({}, None)

        assert captured_items[0]["anomaly_type"] == "noise"

    def test_alert_ttl_is_approximately_90_days_from_now(self):
        """Alert TTL should be approximately now + 90 days."""
        import time as time_module
        reading = _make_reading("pipe_012", "2024-06-15T15:00:00", 90.0, 20.0, "leak")
        raw_item = _make_raw_item("pipe_012", "2024-06-15T15:00:00", 90.0, 20.0, "leak")

        captured_items = []

        def capture_put(table, item):
            captured_items.append(item)

        before = int(time_module.time())

        with patch("backend.detector.handler._fetch_unprocessed_readings",
                   return_value=([reading], [raw_item])), \
             patch("backend.detector.handler.anomaly_model.predict",
                   return_value=[0.9]), \
             patch("backend.detector.handler._mark_processed"), \
             patch("backend.detector.handler.put_item_with_retry", side_effect=capture_put), \
             patch("backend.detector.handler.boto3.resource"):

            from backend.detector.handler import handler
            handler({}, None)

        after = int(time_module.time())
        ttl = captured_items[0]["ttl"]
        expected_ttl = 90 * 86_400
        assert before + expected_ttl <= ttl <= after + expected_ttl + 1
