"""GET /pipes endpoint — list all pipes with pagination."""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter

from backend.app.responses import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/pipes")
def get_pipes(continuation_token: Optional[str] = None) -> dict:
    """Return a paginated list of all pipes."""
    table_prefix = os.environ.get("TABLE_PREFIX", "aquamind")
    table_name = f"{table_prefix}-Pipes"

    try:
        dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        table = dynamodb.Table(table_name)

        kwargs: dict = {"Limit": 100}
        if continuation_token is not None:
            exclusive_start_key = json.loads(base64.b64decode(continuation_token).decode("utf-8"))
            kwargs["ExclusiveStartKey"] = exclusive_start_key

        response = table.scan(**kwargs)
        pipes = response.get("Items", [])

        next_token: Optional[str] = None
        if "LastEvaluatedKey" in response:
            next_token = base64.b64encode(
                json.dumps(response["LastEvaluatedKey"]).encode("utf-8")
            ).decode("utf-8")

    except (BotoCoreError, ClientError) as exc:
        logger.warning("DynamoDB unavailable, returning local store pipes: %s", exc)
        from backend.app import local_store
        pipes = local_store.get_pipes()
        next_token = None

    return success_response({"pipes": pipes, "continuation_token": next_token})
