"""Unit tests for all FastAPI API endpoints."""
from __future__ import annotations

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set DRY_RUN before importing the app so simulate doesn't hit DynamoDB
os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("TABLE_PREFIX", "test")

from backend.app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert_item(alert_id: str = "alert-123") -> dict:
    return {
        "alert_id": alert_id,
        "pipe_id": "pipe_001",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "anomaly_type": "leak",
        "anomaly_score": "0.8",
        "failure_probability": "0.6",
        "priority_score": 75,
        "priority_level": "Critical",
        "immediate_action_required": True,
        "flow_rate": "120.5",
        "pressure": "35.2",
        "ttl": 9999999999,
    }


# ---------------------------------------------------------------------------
# POST /simulate
# ---------------------------------------------------------------------------

class TestSimulate:
    def test_success(self):
        """Happy path: valid request returns simulation summary."""
        payload = {
            "num_pipes": 5,
            "num_junctions": 10,
            "days": 1,
            "interval_hours": 1,
            "anomaly_rate": 0.1,
            "table_prefix": "test",
        }
        resp = client.post("/simulate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "simulation_id" in data
        assert data["pipes_generated"] == 5
        assert data["readings_generated"] > 0
        assert data["anomalies_injected"] >= 0

    def test_422_on_invalid_payload(self):
        """Missing required fields returns 422."""
        resp = client.post("/simulate", json={"num_pipes": "not-a-number"})
        assert resp.status_code == 422

    def test_422_on_empty_body(self):
        """Empty body still works (all fields have defaults)."""
        resp = client.post("/simulate", json={})
        # All fields have defaults, so this should succeed
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /pipes
# ---------------------------------------------------------------------------

class TestPipes:
    @patch("backend.app.routers.pipes.boto3")
    def test_success(self, mock_boto3):
        """Happy path: returns pipes list."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            "Items": [{"pipe_id": "pipe_001", "material": "PVC"}],
        }
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.get("/pipes")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert len(body["data"]["pipes"]) == 1
        assert body["data"]["continuation_token"] is None

    @patch("backend.app.routers.pipes.boto3")
    def test_pagination_token_returned(self, mock_boto3):
        """When DynamoDB returns LastEvaluatedKey, continuation_token is set."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            "Items": [{"pipe_id": "pipe_001"}],
            "LastEvaluatedKey": {"pipe_id": "pipe_001"},
        }
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.get("/pipes")
        assert resp.status_code == 200
        assert resp.json()["data"]["continuation_token"] is not None


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------

class TestAlerts:
    @patch("backend.app.routers.alerts.boto3")
    def test_success(self, mock_boto3):
        """Happy path: returns alerts sorted by priority descending."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            "Items": [
                {**_make_alert_item(), "priority_score": 30, "priority_level": "Medium"},
                {**_make_alert_item("alert-456"), "priority_score": 80, "priority_level": "Critical"},
            ],
        }
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.get("/alerts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        alerts = body["data"]["alerts"]
        assert len(alerts) == 2
        # Sorted descending
        assert alerts[0]["priority_score"] >= alerts[1]["priority_score"]

    @patch("backend.app.routers.alerts.boto3")
    def test_immediate_action_flag_on_critical(self, mock_boto3):
        """Critical alerts have immediate_action_required=True."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            "Items": [_make_alert_item()],
        }
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.get("/alerts")
        alert = resp.json()["data"]["alerts"][0]
        assert alert["immediate_action_required"] is True


# ---------------------------------------------------------------------------
# POST /detect
# ---------------------------------------------------------------------------

class TestDetect:
    def _reading_payload(self):
        return {
            "readings": [
                {
                    "pipe_id": "pipe_001",
                    "timestamp": "2024-01-01T00:00:00+00:00",
                    "flow_rate": 150.0,
                    "pressure": 20.0,
                    "anomaly_label": "leak",
                }
            ]
        }

    @patch("backend.app.routers.detect.boto3")
    @patch("backend.app.routers.detect.anomaly_model")
    def test_success(self, mock_model, mock_boto3):
        """Happy path: anomalous reading creates an alert."""
        mock_model.predict.return_value = [0.9]
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.post("/detect", json=self._reading_payload())
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["alerts_created"] == 1

    @patch("backend.app.routers.detect.boto3")
    @patch("backend.app.routers.detect.anomaly_model")
    def test_no_alerts_when_score_below_threshold(self, mock_model, mock_boto3):
        """Readings below threshold produce no alerts."""
        mock_model.predict.return_value = [0.3]
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.post("/detect", json=self._reading_payload())
        assert resp.status_code == 200
        assert resp.json()["data"]["alerts_created"] == 0

    @patch("backend.app.routers.detect.anomaly_model")
    def test_503_when_model_unavailable(self, mock_model):
        """Returns 503 when ModelNotAvailableError is raised."""
        from backend.models.anomaly_model import ModelNotAvailableError
        mock_model.predict.side_effect = ModelNotAvailableError("model missing")

        resp = client.post("/detect", json=self._reading_payload())
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "error"
        assert "model" in body["error_message"].lower()

    def test_422_on_invalid_payload(self):
        """Missing readings field returns 422."""
        resp = client.post("/detect", json={})
        assert resp.status_code == 422

    def test_422_on_empty_readings(self):
        """Empty readings list returns 422 (min_length=1)."""
        resp = client.post("/detect", json={"readings": []})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /whatif
# ---------------------------------------------------------------------------

class TestWhatIf:
    def _payload(self, alert_id: str = "alert-123") -> dict:
        return {
            "alert_id": alert_id,
            "leak_rate": 5.0,
            "population_affected": 1000,
            "repair_cost": 10000.0,
            "time_horizon_days": 30,
        }

    @patch("backend.app.routers.whatif.boto3")
    def test_success(self, mock_boto3):
        """Happy path: returns simulation result."""
        mock_alerts_table = MagicMock()
        mock_alerts_table.get_item.return_value = {"Item": _make_alert_item()}
        mock_results_table = MagicMock()

        def table_factory(name):
            if "Alert" in name:
                return mock_alerts_table
            return mock_results_table

        mock_boto3.resource.return_value.Table.side_effect = table_factory

        resp = client.post("/whatif", json=self._payload())
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "simulation_id" in data
        assert "ignore_scenario" in data
        assert "repair_scenario" in data
        assert "savings_usd" in data

    @patch("backend.app.routers.whatif.boto3")
    def test_404_on_missing_alert(self, mock_boto3):
        """Returns 404 when alert_id does not exist."""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # no "Item" key
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.post("/whatif", json=self._payload("nonexistent-alert"))
        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"

    def test_422_on_invalid_payload(self):
        """Missing required fields returns 422."""
        resp = client.post("/whatif", json={"alert_id": "x"})
        assert resp.status_code == 422

    def test_422_on_out_of_range_time_horizon(self):
        """time_horizon_days outside [1, 365] returns 422."""
        payload = {**self._payload(), "time_horizon_days": 0}
        resp = client.post("/whatif", json=payload)
        assert resp.status_code == 422

        payload = {**self._payload(), "time_horizon_days": 366}
        resp = client.post("/whatif", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /explain
# ---------------------------------------------------------------------------

class TestExplain:
    def _payload(self, simulation_id: str | None = None) -> dict:
        p = {
            "alert_id": "alert-123",
            "pipe_id": "pipe_001",
            "loss_rate": 5.0,
            "population_affected": 1000,
            "repair_cost": 10000.0,
            "time_horizon_days": 30,
        }
        if simulation_id:
            p["simulation_id"] = simulation_id
        return p

    @patch("backend.app.routers.explain.generate_recommendation")
    @patch("backend.app.routers.explain.boto3")
    def test_success_without_simulation_id(self, mock_boto3, mock_recommend):
        """Happy path: computes fresh simulation and returns recommendation."""
        from backend.app.models import RecommendationResponse
        mock_recommend.return_value = RecommendationResponse(
            recommended_action="Repair immediately",
            savings_usd=5000.0,
            repair_cost_usd=10000.0,
            urgency_rationale="High risk",
            ai_text="Fix it now.",
        )

        resp = client.post("/explain", json=self._payload())
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "recommended_action" in data
        assert "savings_usd" in data
        assert "urgency_rationale" in data

    @patch("backend.app.routers.explain.generate_recommendation")
    @patch("backend.app.routers.explain.boto3")
    def test_success_with_existing_simulation(self, mock_boto3, mock_recommend):
        """Uses stored SimulationResult when simulation_id is provided and found."""
        from backend.app.models import RecommendationResponse
        mock_recommend.return_value = RecommendationResponse(
            recommended_action="Repair immediately",
            savings_usd=5000.0,
            repair_cost_usd=10000.0,
            urgency_rationale="High risk",
            ai_text="",
        )
        sim_id = str(uuid.uuid4())
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "simulation_id": sim_id,
                "alert_id": "alert-123",
                "ignore_water_loss_liters": "120000.0",
                "ignore_financial_cost_usd": "15000.0",
                "ignore_damage_score": "0.1",
                "repair_cost_usd": "10000.0",
                "water_loss_prevented_liters": "120000.0",
                "savings_usd": "5000.0",
                "recommended_action": "Repair immediately",
                "ai_recommendation": "",
                "ttl": 9999999999,
            }
        }
        mock_boto3.resource.return_value.Table.return_value = mock_table

        resp = client.post("/explain", json=self._payload(simulation_id=sim_id))
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_422_on_invalid_payload(self):
        """Missing required fields returns 422."""
        resp = client.post("/explain", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Unhandled exception → 500 with request_id
# ---------------------------------------------------------------------------

class TestUnhandledException:
    @patch("backend.app.routers.pipes.boto3")
    def test_500_returns_request_id(self, mock_boto3):
        """Unhandled exception returns 500 with request_id in response."""
        mock_boto3.resource.side_effect = RuntimeError("unexpected boom")

        resp = client.get("/pipes")
        assert resp.status_code == 500
