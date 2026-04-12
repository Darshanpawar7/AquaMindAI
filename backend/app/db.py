"""DynamoDB client utilities with retry logic and pagination support."""

import base64
import json
import time
from typing import Any


def put_item_with_retry(table: Any, item: dict, max_retries: int = 3) -> None:
    """Write an item to DynamoDB with exponential backoff retry.

    Retries up to max_retries times with backoff: 100ms, 200ms, 400ms.
    Raises the last exception after exhausting retries.
    """
    delay = 0.1  # 100ms initial backoff
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            table.put_item(Item=item)
            return
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2

    raise last_exc  # type: ignore[misc]


def query_with_pagination(
    table: Any,
    key_condition: Any,
    limit: int = 100,
    continuation_token: str | None = None,
) -> tuple[list, str | None]:
    """Query DynamoDB with pagination support.

    Args:
        table: boto3 DynamoDB Table resource.
        key_condition: KeyConditionExpression for the query.
        limit: Maximum number of items to return per page.
        continuation_token: Base64-encoded JSON ExclusiveStartKey from a previous call.

    Returns:
        (items, next_token) where next_token is None if no more pages.
    """
    kwargs: dict[str, Any] = {
        "KeyConditionExpression": key_condition,
        "Limit": limit,
    }

    if continuation_token is not None:
        exclusive_start_key = json.loads(
            base64.b64decode(continuation_token).decode("utf-8")
        )
        kwargs["ExclusiveStartKey"] = exclusive_start_key

    response = table.query(**kwargs)
    items = response.get("Items", [])

    next_token: str | None = None
    if "LastEvaluatedKey" in response:
        next_token = base64.b64encode(
            json.dumps(response["LastEvaluatedKey"]).encode("utf-8")
        ).decode("utf-8")

    return items, next_token
