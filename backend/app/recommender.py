"""Recommendation engine for AquaMind AI — wraps Amazon Bedrock (Claude)."""
from __future__ import annotations

import json
import logging

import boto3

from backend.app.models import RecommendationResponse, SimulationResult

logger = logging.getLogger(__name__)

_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def _build_prompt(
    pipe_id: str,
    loss_rate: float,
    population_affected: int,
    repair_cost: float,
    time_horizon: int,
    simulation_result: SimulationResult,
) -> str:
    ignore_water_loss = simulation_result.ignore_scenario.total_water_loss_liters
    ignore_cost = simulation_result.ignore_scenario.financial_cost_usd
    repair_cost_usd = simulation_result.repair_scenario.repair_cost_usd
    savings = simulation_result.savings_usd

    return (
        f"Given a leak in pipe {pipe_id}, loss rate {loss_rate} m³/h, "
        f"population affected {population_affected}, "
        f"and repair cost ${repair_cost}, calculate the impact of ignoring vs repairing "
        f"over {time_horizon} days.\n"
        f"Ignore scenario: water loss {ignore_water_loss}L, cost ${ignore_cost}. "
        f"Repair scenario: cost ${repair_cost_usd}, savings ${savings}.\n"
        f"Return a concise recommendation with urgency rationale."
    )


def generate_recommendation(
    pipe_id: str,
    loss_rate: float,
    population_affected: int,
    repair_cost: float,
    time_horizon: int,
    simulation_result: SimulationResult,
) -> RecommendationResponse:
    """Generate an AI-powered repair recommendation via Amazon Bedrock.

    Falls back to a deterministic recommendation from simulation_result if
    Bedrock is unavailable or returns an error.

    Args:
        pipe_id: Identifier of the pipe with the detected leak.
        loss_rate: Leak rate in m³/h.
        population_affected: Number of people affected.
        repair_cost: Estimated repair cost in USD.
        time_horizon: Projection window in days.
        simulation_result: Pre-computed impact simulation result.

    Returns:
        RecommendationResponse with all five required fields populated.
    """
    prompt = _build_prompt(
        pipe_id, loss_rate, population_affected, repair_cost, time_horizon, simulation_result
    )

    try:
        client = boto3.client("bedrock-runtime")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = client.invoke_model(modelId=_MODEL_ID, body=body)
        response_body = json.loads(response["body"].read())
        ai_text = response_body["content"][0]["text"]

        return RecommendationResponse(
            recommended_action=simulation_result.recommended_action,
            savings_usd=simulation_result.savings_usd,
            repair_cost_usd=simulation_result.repair_scenario.repair_cost_usd,
            urgency_rationale=ai_text,
            ai_text=ai_text,
        )

    except Exception as exc:
        logger.error("Bedrock invocation failed for pipe %s: %s", pipe_id, exc)
        urgency_rationale = (
            f"Based on {time_horizon}-day projection: "
            f"{simulation_result.ignore_scenario.financial_cost_usd:.2f} USD at risk"
        )
        return RecommendationResponse(
            recommended_action=simulation_result.recommended_action,
            savings_usd=simulation_result.savings_usd,
            repair_cost_usd=simulation_result.repair_scenario.repair_cost_usd,
            urgency_rationale=urgency_rationale,
            ai_text="",
        )
