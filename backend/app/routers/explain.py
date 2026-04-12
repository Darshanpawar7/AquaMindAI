"""POST /explain endpoint — generate AI recommendation via Bedrock."""
from __future__ import annotations

import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from fastapi import APIRouter

from backend.app import local_store
from backend.app.recommender import generate_recommendation
from backend.app.responses import success_response
from backend.app.schemas import ExplainRequest
from backend.app.simulator import compute_impact

router = APIRouter()


@router.post("/explain")
def explain(request: ExplainRequest) -> dict:
    """Generate an AI-powered repair recommendation."""
    table_prefix = os.environ.get("TABLE_PREFIX", "aquamind")
    results_table_name = f"{table_prefix}-SimulationResults"

    simulation_result = None

    # Try to fetch existing SimulationResult if simulation_id provided
    if request.simulation_id:
        # Try DynamoDB first
        try:
            dynamodb = boto3.resource(
                "dynamodb",
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            results_table = dynamodb.Table(results_table_name)
            response = results_table.get_item(Key={"simulation_id": request.simulation_id})
            if "Item" in response:
                item = response["Item"]
                from backend.app.models import IgnoreScenario, RepairScenario, SimulationResult
                simulation_result = SimulationResult(
                    simulation_id=item["simulation_id"],
                    alert_id=item["alert_id"],
                    ignore_scenario=IgnoreScenario(
                        total_water_loss_liters=float(item["ignore_water_loss_liters"]),
                        financial_cost_usd=float(item["ignore_financial_cost_usd"]),
                        infrastructure_damage_score=float(item["ignore_damage_score"]),
                    ),
                    repair_scenario=RepairScenario(
                        repair_cost_usd=float(item["repair_cost_usd"]),
                        water_loss_prevented_liters=float(item["water_loss_prevented_liters"]),
                    ),
                    savings_usd=float(item["savings_usd"]),
                    recommended_action=item["recommended_action"],
                    ai_recommendation=item.get("ai_recommendation", ""),
                    ttl=int(item["ttl"]) if item.get("ttl") else None,
                )
        except (BotoCoreError, ClientError, NoCredentialsError, Exception):
            # Fall back to local store
            item = local_store.get_simulation_result(request.simulation_id)
            if item:
                from backend.app.models import IgnoreScenario, RepairScenario, SimulationResult
                simulation_result = SimulationResult(
                    simulation_id=item["simulation_id"],
                    alert_id=item["alert_id"],
                    ignore_scenario=IgnoreScenario(
                        total_water_loss_liters=float(item["ignore_water_loss_liters"]),
                        financial_cost_usd=float(item["ignore_financial_cost_usd"]),
                        infrastructure_damage_score=float(item["ignore_damage_score"]),
                    ),
                    repair_scenario=RepairScenario(
                        repair_cost_usd=float(item["repair_cost_usd"]),
                        water_loss_prevented_liters=float(item["water_loss_prevented_liters"]),
                    ),
                    savings_usd=float(item["savings_usd"]),
                    recommended_action=item["recommended_action"],
                    ai_recommendation=item.get("ai_recommendation", ""),
                    ttl=int(item["ttl"]) if item.get("ttl") else None,
                )

    # Compute fresh if not found in DB or local store
    if simulation_result is None:
        simulation_result = compute_impact(
            alert_id=request.alert_id,
            leak_rate=request.loss_rate,
            population_affected=request.population_affected,
            repair_cost=request.repair_cost,
            time_horizon_days=request.time_horizon_days,
        )

    recommendation = generate_recommendation(
        pipe_id=request.pipe_id,
        loss_rate=request.loss_rate,
        population_affected=request.population_affected,
        repair_cost=request.repair_cost,
        time_horizon=request.time_horizon_days,
        simulation_result=simulation_result,
    )

    return success_response({
        "recommended_action": recommendation.recommended_action,
        "savings_usd": recommendation.savings_usd,
        "repair_cost_usd": recommendation.repair_cost_usd,
        "urgency_rationale": recommendation.urgency_rationale,
        "ai_text": recommendation.ai_text,
    })
