"""Unit tests for backend/app/recommender.py."""
from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from backend.app.models import (
    IgnoreScenario,
    RepairScenario,
    RecommendationResponse,
    SimulationResult,
)
from backend.app.recommender import generate_recommendation, _build_prompt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_simulation_result(
    recommended_action: str = "Repair immediately",
    savings_usd: float = 5000.0,
    repair_cost_usd: float = 1200.0,
    financial_cost_usd: float = 6200.0,
    total_water_loss_liters: float = 86400.0,
) -> SimulationResult:
    return SimulationResult(
        simulation_id="sim-001",
        alert_id="alert-001",
        ignore_scenario=IgnoreScenario(
            total_water_loss_liters=total_water_loss_liters,
            financial_cost_usd=financial_cost_usd,
            infrastructure_damage_score=0.3,
        ),
        repair_scenario=RepairScenario(
            repair_cost_usd=repair_cost_usd,
            water_loss_prevented_liters=total_water_loss_liters,
        ),
        savings_usd=savings_usd,
        recommended_action=recommended_action,
    )


def _make_bedrock_response(text: str) -> MagicMock:
    """Build a mock boto3 invoke_model response."""
    body_bytes = json.dumps({"content": [{"text": text}]}).encode()
    mock_response = MagicMock()
    mock_response["body"].read.return_value = body_bytes
    # Support dict-style access on the mock
    mock_response.__getitem__ = lambda self, key: (
        MagicMock(read=lambda: body_bytes) if key == "body" else MagicMock()
    )
    return mock_response


# ---------------------------------------------------------------------------
# Bedrock success path
# ---------------------------------------------------------------------------

def test_bedrock_success_returns_all_fields():
    """Mock boto3 client; verify parsed recommendation returned with all fields."""
    sim = _make_simulation_result()
    ai_text = "Repair pipe_042 immediately to avoid $6200 in losses."

    body_payload = json.dumps({"content": [{"text": ai_text}]}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_payload

    mock_response = {"body": mock_body}

    mock_client = MagicMock()
    mock_client.invoke_model.return_value = mock_response

    with patch("backend.app.recommender.boto3.client", return_value=mock_client):
        result = generate_recommendation(
            pipe_id="pipe_042",
            loss_rate=3.5,
            population_affected=200,
            repair_cost=1200.0,
            time_horizon=30,
            simulation_result=sim,
        )

    assert isinstance(result, RecommendationResponse)
    assert result.recommended_action == sim.recommended_action
    assert result.savings_usd == sim.savings_usd
    assert result.repair_cost_usd == sim.repair_scenario.repair_cost_usd
    assert result.urgency_rationale == ai_text
    assert result.ai_text == ai_text


# ---------------------------------------------------------------------------
# Bedrock error / fallback path
# ---------------------------------------------------------------------------

def test_bedrock_error_returns_fallback_with_all_required_fields():
    """Mock boto3 to raise exception; verify fallback has all required fields."""
    sim = _make_simulation_result(
        recommended_action="Repair immediately",
        savings_usd=4800.0,
        repair_cost_usd=1500.0,
        financial_cost_usd=6300.0,
    )

    mock_client = MagicMock()
    mock_client.invoke_model.side_effect = Exception("Bedrock unavailable")

    with patch("backend.app.recommender.boto3.client", return_value=mock_client):
        result = generate_recommendation(
            pipe_id="pipe_007",
            loss_rate=2.0,
            population_affected=150,
            repair_cost=1500.0,
            time_horizon=14,
            simulation_result=sim,
        )

    assert isinstance(result, RecommendationResponse)
    # All five fields must be present
    assert result.recommended_action, "recommended_action must be non-empty"
    assert result.savings_usd is not None
    assert result.repair_cost_usd is not None
    assert result.urgency_rationale, "urgency_rationale must be non-empty on fallback"
    # ai_text is empty on fallback
    assert result.ai_text == ""

    # Values come from simulation_result
    assert result.recommended_action == sim.recommended_action
    assert result.savings_usd == sim.savings_usd
    assert result.repair_cost_usd == sim.repair_scenario.repair_cost_usd
    assert "14-day" in result.urgency_rationale
    assert "6300.00" in result.urgency_rationale


# ---------------------------------------------------------------------------
# Prompt content verification
# ---------------------------------------------------------------------------

def test_prompt_contains_all_required_context():
    """Verify prompt contains pipe_id, loss_rate, population_affected, repair_cost, time_horizon."""
    sim = _make_simulation_result()
    prompt = _build_prompt(
        pipe_id="pipe_099",
        loss_rate=7.25,
        population_affected=500,
        repair_cost=3000.0,
        time_horizon=60,
        simulation_result=sim,
    )

    assert "pipe_099" in prompt
    assert "7.25" in prompt
    assert "500" in prompt
    assert "3000" in prompt
    assert "60" in prompt
