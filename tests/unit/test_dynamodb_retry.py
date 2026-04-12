"""Unit tests for DynamoDB retry logic and pagination (Requirement 9.4)."""

import base64
import json
from unittest.mock import MagicMock, call, patch

import pytest

from backend.app.db import put_item_with_retry, query_with_pagination


# ---------------------------------------------------------------------------
# put_item_with_retry tests
# ---------------------------------------------------------------------------


def test_put_item_success_on_first_try():
    """Item written successfully on the first attempt — table called exactly once."""
    table = MagicMock()
    item = {"pipe_id": "pipe_001", "value": 42}

    put_item_with_retry(table, item)

    table.put_item.assert_called_once_with(Item=item)


def test_put_item_success_after_two_failures():
    """Item written on the 3rd attempt after 2 consecutive failures."""
    table = MagicMock()
    error = RuntimeError("DynamoDB unavailable")
    table.put_item.side_effect = [error, error, None]
    item = {"pipe_id": "pipe_002"}

    with patch("time.sleep") as mock_sleep:
        put_item_with_retry(table, item)

    assert table.put_item.call_count == 3
    # Backoff: 100ms then 200ms
    mock_sleep.assert_has_calls([call(0.1), call(0.2)])


def test_put_item_raises_after_three_failures():
    """Exception raised after 3 consecutive failures; retry count equals 3."""
    table = MagicMock()
    error = RuntimeError("persistent failure")
    table.put_item.side_effect = error
    item = {"pipe_id": "pipe_003"}

    with patch("time.sleep"):
        with pytest.raises(RuntimeError, match="persistent failure"):
            put_item_with_retry(table, item)

    assert table.put_item.call_count == 3


def test_put_item_no_sleep_on_last_failure():
    """sleep is called only between retries, not after the final failure."""
    table = MagicMock()
    table.put_item.side_effect = RuntimeError("fail")

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError):
            put_item_with_retry(table, item={"k": "v"}, max_retries=3)

    # 3 attempts → 2 sleeps (between attempt 1→2 and 2→3)
    assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# query_with_pagination tests
# ---------------------------------------------------------------------------


def test_query_no_continuation_token_no_next_page():
    """Single-page query returns items and None next_token."""
    table = MagicMock()
    table.query.return_value = {"Items": [{"id": "1"}, {"id": "2"}]}
    key_cond = MagicMock()

    items, next_token = query_with_pagination(table, key_cond, limit=10)

    assert items == [{"id": "1"}, {"id": "2"}]
    assert next_token is None
    table.query.assert_called_once_with(KeyConditionExpression=key_cond, Limit=10)


def test_query_returns_next_token_when_last_evaluated_key_present():
    """next_token is base64-encoded JSON of LastEvaluatedKey."""
    table = MagicMock()
    last_key = {"pipe_id": "pipe_010", "timestamp": "2024-01-01T00:00:00"}
    table.query.return_value = {"Items": [{"id": "x"}], "LastEvaluatedKey": last_key}
    key_cond = MagicMock()

    items, next_token = query_with_pagination(table, key_cond)

    assert next_token is not None
    decoded = json.loads(base64.b64decode(next_token).decode("utf-8"))
    assert decoded == last_key


def test_query_with_continuation_token_passes_exclusive_start_key():
    """Continuation token is decoded and passed as ExclusiveStartKey."""
    table = MagicMock()
    table.query.return_value = {"Items": []}
    key_cond = MagicMock()

    start_key = {"pipe_id": "pipe_020", "timestamp": "2024-06-01T00:00:00"}
    token = base64.b64encode(json.dumps(start_key).encode("utf-8")).decode("utf-8")

    query_with_pagination(table, key_cond, continuation_token=token)

    table.query.assert_called_once_with(
        KeyConditionExpression=key_cond,
        Limit=100,
        ExclusiveStartKey=start_key,
    )
