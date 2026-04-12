"""GET /alerts endpoint — list alerts sorted by priority_score descending."""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoRegionError
from fastapi import APIRouter

from backend.app.responses import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/alerts")
def get_alerts(continuation_token: Optional[str] = None) -> dict:
    """Return a paginated list of alerts sorted by priority_score descending."""
    table_prefix = os.environ.get("TABLE_PREFIX", "aquamind")
    table_name = f"{table_prefix}-Alerts"

    try:
        dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        table = dynamodb.Table(table_name)

        kwargs: dict = {"Limit": 100}
        if continuation_token is not None:
            exclusive_start_key = json.loads(base64.b64decode(continuation_token).decode("utf-8"))
            kwargs["ExclusiveStartKey"] = exclusive_start_key

        response = table.scan(**kwargs)
        alerts = response.get("Items", [])

        # Sort by priority_score descending (in-page sort)
        alerts.sort(key=lambda a: int(a.get("priority_score", 0)), reverse=True)

        # Ensure immediate_action_required flag is present
        for alert in alerts:
            if "immediate_action_required" not in alert:
                alert["immediate_action_required"] = alert.get("priority_level") == "Critical"

        next_token: Optional[str] = None
        if "LastEvaluatedKey" in response:
            next_token = base64.b64encode(
                json.dumps(response["LastEvaluatedKey"]).encode("utf-8")
            ).decode("utf-8")

    except (BotoCoreError, ClientError) as exc:
        logger.warning("DynamoDB unavailable, returning local store alerts: %s", exc)
        from backend.app import local_store
        alerts = local_store.get_alerts()
        alerts.sort(key=lambda a: int(a.get("priority_score", 0)), reverse=True)
        for alert in alerts:
            if "immediate_action_required" not in alert:
                alert["immediate_action_required"] = alert.get("priority_level") == "Critical"
        next_token = None

    return success_response({"alerts": alerts, "continuation_token": next_token})
