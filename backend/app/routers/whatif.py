"""POST /whatif endpoint — run impact simulation for an alert."""
from __future__ import annotations

import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app import local_store
from backend.app.db import put_item_with_retry
from backend.app.responses import error_response, success_response
from backend.app.schemas import WhatIfRequest
from backend.app.simulator import compute_impact

router = APIRouter()


@router.post("/whatif")
def whatif(request: WhatIfRequest) -> dict:
    """Compute ignore vs. repair impact for an alert and persist the result."""
    table_prefix = os.environ.get("TABLE_PREFIX", "aquamind")
    alerts_table_name = f"{table_prefix}-Alerts"
    results_table_name = f"{table_prefix}-SimulationResults"

    # Verify alert exists — try DynamoDB first, fall back to local store
    alert_found = False
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )
        alerts_table = dynamodb.Table(alerts_table_name)
        response = alerts_table.get_item(Key={"alert_id": request.alert_id})
        alert_found = "Item" in response
    except (BotoCoreError, ClientError, NoCredentialsError, Exception):
        # Fall back to local store
        alert_found = local_store.get_alert(request.alert_id) is not None

    if not alert_found:
        return JSONResponse(
            status_code=404,
            content=error_response(f"Alert '{request.alert_id}' not found."),
        )

    # Compute impact
    result = compute_impact(
        alert_id=request.alert_id,
        leak_rate=request.leak_rate,
        population_affected=request.population_affected,
        repair_cost=request.repair_cost,
        time_horizon_days=request.time_horizon_days,
    )

    # Persist SimulationResult — try DynamoDB, fall back to local store
    item = {
        "simulation_id": result.simulation_id,
        "alert_id": result.alert_id,
        "ignore_water_loss_liters": str(result.ignore_scenario.total_water_loss_liters),
        "ignore_financial_cost_usd": str(result.ignore_scenario.financial_cost_usd),
        "ignore_damage_score": str(result.ignore_scenario.infrastructure_damage_score),
        "repair_cost_usd": str(result.repair_scenario.repair_cost_usd),
        "water_loss_prevented_liters": str(result.repair_scenario.water_loss_prevented_liters),
        "savings_usd": str(result.savings_usd),
        "recommended_action": result.recommended_action,
        "ai_recommendation": result.ai_recommendation,
        "ttl": result.ttl,
    }
    try:
        results_table = dynamodb.Table(results_table_name)
        put_item_with_retry(results_table, item)
    except Exception:
        local_store.add_simulation_result(item)

    return success_response({
        "simulation_id": result.simulation_id,
        "alert_id": result.alert_id,
        "ignore_scenario": {
            "total_water_loss_liters": result.ignore_scenario.total_water_loss_liters,
            "financial_cost_usd": result.ignore_scenario.financial_cost_usd,
            "infrastructure_damage_score": result.ignore_scenario.infrastructure_damage_score,
        },
        "repair_scenario": {
            "repair_cost_usd": result.repair_scenario.repair_cost_usd,
            "water_loss_prevented_liters": result.repair_scenario.water_loss_prevented_liters,
        },
        "savings_usd": result.savings_usd,
        "recommended_action": result.recommended_action,
    })
