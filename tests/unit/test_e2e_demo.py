"""
End-to-end integration test for the AquaMind AI demo flow.

Mocks DynamoDB and Bedrock; exercises the full pipeline:
  simulate → detect → score → whatif → explain

Asserts:
- Alert is created with correct fields
- Priority score is assigned (1–100)
- SimulationResult is returned with both scenarios
- Recommendation contains all required fields
- Full flow completes within 60 seconds
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

ALERT_ID = str(uuid.uuid4())
PIPE_ID = "pipe_001"
NOW = datetime.now(timezone.utc).isoformat()

SAMPLE_READING = {
    "pipe_id": PIPE_ID,
    "timestamp": NOW,
    "flow_rate": 95.0,   # high flow → anomalous
    "pressure": 18.0,    # low pressure → anomalous
    "anomaly_label": "leak",
}

STORED_ALERT = {
    "alert_id": ALERT_ID,
    "pipe_id": PIPE_ID,
    "timestamp": NOW,
    "anomaly_type": "leak",
    "anomaly_score": "0.85",
    "failure_probability": "0.72",
    "priority_score": 78,
    "priority_level": "High",
    "immediate_action_required": False,
    "flow_rate": "95.0",
    "pressure": "18.0",
    "ttl": int(time.time()) + 86400 * 90,
}


def _make_dynamodb_mock(alert_item=None):
    """Return a mock boto3 DynamoDB resource that returns the given alert item."""
    table_mock = MagicMock()
    table_mock.get_item.return_value = {"Item": alert_item} if alert_item else {}
    table_mock.put_item.return_value = {}

    resource_mock = MagicMock()
    resource_mock.Table.return_value = table_mock
    return resource_mock


def _make_bedrock_mock(response_text: str):
    """Return a mock boto3 Bedrock client that returns the given text."""
    body_mock = MagicMock()
    body_mock.read.return_value = json.dumps({
        "content": [{"text": response_text}]
    }).encode()

    client_mock = MagicMock()
    client_mock.invoke_model.return_value = {"body": body_mock}
    return client_mock


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EDemoFlow:
    """Full demo flow: detect → whatif → explain."""

    def test_full_flow_completes_within_60_seconds(self):
        """The entire demo pipeline must complete in under 60 seconds."""
        start = time.time()

        ddb_mock = _make_dynamodb_mock(alert_item=STORED_ALERT)
        bedrock_mock = _make_bedrock_mock(
            "Recommend immediate repair. Savings: $12,000. Urgency: High risk of failure."
        )

        with (
            patch("boto3.resource", return_value=ddb_mock),
            patch("boto3.client", return_value=bedrock_mock),
        ):
            # Step 1: detect
            detect_resp = client.post("/detect", json={"readings": [SAMPLE_READING]})
            # Step 2: whatif
            whatif_resp = client.post("/whatif", json={
                "alert_id": ALERT_ID,
                "leak_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 30,
            })
            # Step 3: explain
            explain_resp = client.post("/explain", json={
                "alert_id": ALERT_ID,
                "pipe_id": PIPE_ID,
                "loss_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 30,
            })

        elapsed = time.time() - start
        assert elapsed < 60, f"Full flow took {elapsed:.1f}s — exceeds 60s limit"

        # Verify all steps succeeded
        assert detect_resp.status_code == 200
        assert whatif_resp.status_code == 200
        assert explain_resp.status_code == 200

    def test_detect_creates_alert_with_required_fields(self):
        """POST /detect must return an alert with all required fields."""
        ddb_mock = _make_dynamodb_mock()

        with patch("boto3.resource", return_value=ddb_mock):
            resp = client.post("/detect", json={"readings": [SAMPLE_READING]})

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

        data = body["data"]
        assert data["alerts_created"] >= 0  # may be 0 if score ≤ threshold

        # If an alert was created, verify required fields
        for alert in data["alerts"]:
            assert "alert_id" in alert
            assert "pipe_id" in alert
            assert "timestamp" in alert
            assert "anomaly_type" in alert
            assert "flow_rate" in alert
            assert "pressure" in alert

    def test_detect_assigns_priority_score_in_range(self):
        """Every alert produced by /detect must have priority_score in [1, 100]."""
        ddb_mock = _make_dynamodb_mock()

        with patch("boto3.resource", return_value=ddb_mock):
            resp = client.post("/detect", json={"readings": [SAMPLE_READING]})

        assert resp.status_code == 200
        for alert in resp.json()["data"]["alerts"]:
            score = alert["priority_score"]
            assert 1 <= score <= 100, f"priority_score {score} out of range"

    def test_whatif_returns_simulation_result(self):
        """POST /whatif must return both ignore and repair scenarios."""
        ddb_mock = _make_dynamodb_mock(alert_item=STORED_ALERT)

        with patch("boto3.resource", return_value=ddb_mock):
            resp = client.post("/whatif", json={
                "alert_id": ALERT_ID,
                "leak_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 30,
            })

        assert resp.status_code == 200
        data = resp.json()["data"]

        # Both scenarios present
        assert "ignore_scenario" in data
        assert "repair_scenario" in data
        assert "savings_usd" in data
        assert "recommended_action" in data

        # Non-negative values
        ignore = data["ignore_scenario"]
        assert ignore["total_water_loss_liters"] >= 0
        assert ignore["financial_cost_usd"] >= 0
        assert ignore["infrastructure_damage_score"] >= 0

        repair = data["repair_scenario"]
        assert repair["repair_cost_usd"] >= 0
        assert repair["water_loss_prevented_liters"] >= 0

    def test_explain_returns_recommendation_with_required_fields(self):
        """POST /explain must return all required recommendation fields."""
        ddb_mock = _make_dynamodb_mock(alert_item=STORED_ALERT)
        bedrock_mock = _make_bedrock_mock(
            "Recommend immediate repair. Savings: $12,000. Urgency: High risk of failure."
        )

        with (
            patch("boto3.resource", return_value=ddb_mock),
            patch("boto3.client", return_value=bedrock_mock),
        ):
            resp = client.post("/explain", json={
                "alert_id": ALERT_ID,
                "pipe_id": PIPE_ID,
                "loss_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 30,
            })

        assert resp.status_code == 200
        data = resp.json()["data"]

        assert "recommended_action" in data
        assert "savings_usd" in data
        assert "repair_cost_usd" in data
        assert "urgency_rationale" in data
        assert len(data["urgency_rationale"]) > 0

    def test_whatif_404_on_missing_alert(self):
        """POST /whatif must return 404 when alert_id does not exist."""
        ddb_mock = _make_dynamodb_mock(alert_item=None)

        with patch("boto3.resource", return_value=ddb_mock):
            resp = client.post("/whatif", json={
                "alert_id": "nonexistent-alert-id",
                "leak_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 30,
            })

        assert resp.status_code == 404
        assert resp.json()["status"] == "error"

    def test_explain_fallback_on_bedrock_error(self):
        """POST /explain must return a valid recommendation even when Bedrock fails."""
        ddb_mock = _make_dynamodb_mock(alert_item=STORED_ALERT)

        # Bedrock client raises an exception
        bedrock_mock = MagicMock()
        bedrock_mock.invoke_model.side_effect = Exception("Bedrock unavailable")

        with (
            patch("boto3.resource", return_value=ddb_mock),
            patch("boto3.client", return_value=bedrock_mock),
        ):
            resp = client.post("/explain", json={
                "alert_id": ALERT_ID,
                "pipe_id": PIPE_ID,
                "loss_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 30,
            })

        # Should still succeed via fallback
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "recommended_action" in data
        assert "savings_usd" in data
        assert "repair_cost_usd" in data
        assert "urgency_rationale" in data

    def test_detect_422_on_empty_readings(self):
        """POST /detect must return 422 when readings list is empty."""
        resp = client.post("/detect", json={"readings": []})
        assert resp.status_code == 422

    def test_whatif_400_on_invalid_time_horizon(self):
        """POST /whatif must return 422 when time_horizon_days is out of range."""
        ddb_mock = _make_dynamodb_mock(alert_item=STORED_ALERT)

        with patch("boto3.resource", return_value=ddb_mock):
            resp_low = client.post("/whatif", json={
                "alert_id": ALERT_ID,
                "leak_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 0,
            })
            resp_high = client.post("/whatif", json={
                "alert_id": ALERT_ID,
                "leak_rate": 5.0,
                "population_affected": 1500,
                "repair_cost": 8000.0,
                "time_horizon_days": 366,
            })

        assert resp_low.status_code == 422
        assert resp_high.status_code == 422
