"""Scheduled Lambda handler for AquaMind AI anomaly detection.

Queries unprocessed Readings from DynamoDB, runs the Isolation Forest model,
creates Alert records for anomalous readings, and marks readings as processed.
"""
from __future__ import annotations

import os
import time
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

from backend.app.db import put_item_with_retry
from backend.app.models import Alert, Reading
from backend.models import anomaly_model
from backend.models.anomaly_model import ModelNotAvailableError
from backend.models.priority_scorer import assign_priority_level, compute_priority_score
from backend.models.risk_predictor import predict_failure_probability

_ANOMALY_THRESHOLD = 0.5
_TTL_DAYS = 90
_SECONDS_PER_DAY = 86_400


def handler(event, context):
    """Lambda entry point — process unprocessed Readings and create Alerts.

    Returns:
        {"processed": N, "alerts_created": N}
    """
    table_prefix = os.environ.get("TABLE_PREFIX", "aquamind")
    dynamodb = boto3.resource("dynamodb")
    readings_table = dynamodb.Table(f"{table_prefix}-Readings")
    alerts_table = dynamodb.Table(f"{table_prefix}-Alerts")

    # 1. Query unprocessed readings via GSI
    readings, raw_items = _fetch_unprocessed_readings(readings_table)

    if not readings:
        return {"processed": 0, "alerts_created": 0}

    # 2. Run anomaly model
    try:
        scores = anomaly_model.predict(readings)
    except ModelNotAvailableError as exc:
        raise RuntimeError(f"Model not available: {exc}") from exc

    ttl = int(time.time()) + _TTL_DAYS * _SECONDS_PER_DAY
    alerts_created = 0

    # 3 & 4 & 5. Create alerts for anomalous readings, mark processed, write alerts
    for reading, score, raw_item in zip(readings, scores, raw_items):
        # Mark reading as processed regardless of score
        _mark_processed(readings_table, reading.pipe_id, reading.timestamp)

        if score <= _ANOMALY_THRESHOLD:
            continue

        # Build alert
        risk_result = predict_failure_probability(
            alert_frequency_7d=None,
            anomaly_severity_avg=score,
            pipe_age_years=None,
        )
        failure_prob = risk_result["failure_probability"]
        priority_score = compute_priority_score(
            anomaly_score=score,
            population_factor=score,
            repair_cost_factor=score,
        )
        priority_level = assign_priority_level(failure_prob)

        alert = Alert(
            alert_id=str(uuid.uuid4()),
            pipe_id=reading.pipe_id,
            timestamp=reading.timestamp,
            anomaly_type=reading.anomaly_label if reading.anomaly_label != "normal" else "noise",
            anomaly_score=score,
            failure_probability=failure_prob,
            priority_score=priority_score,
            priority_level=priority_level,
            immediate_action_required=(priority_level == "Critical"),
            flow_rate=reading.flow_rate,
            pressure=reading.pressure,
            ttl=ttl,
        )

        item = {
            "alert_id": alert.alert_id,
            "pipe_id": alert.pipe_id,
            "timestamp": alert.timestamp,
            "anomaly_type": alert.anomaly_type,
            "anomaly_score": str(alert.anomaly_score),
            "failure_probability": str(alert.failure_probability),
            "priority_score": alert.priority_score,
            "priority_level": alert.priority_level,
            "immediate_action_required": alert.immediate_action_required,
            "flow_rate": str(alert.flow_rate),
            "pressure": str(alert.pressure),
            "ttl": alert.ttl,
        }
        put_item_with_retry(alerts_table, item)
        alerts_created += 1

    return {"processed": len(readings), "alerts_created": alerts_created}


def _fetch_unprocessed_readings(readings_table) -> tuple[list[Reading], list[dict]]:
    """Query the processed-timestamp-index GSI for unprocessed readings."""
    response = readings_table.query(
        IndexName="processed-timestamp-index",
        KeyConditionExpression=Key("processed").eq(False),
    )
    raw_items = response.get("Items", [])

    readings = [
        Reading(
            pipe_id=item["pipe_id"],
            timestamp=item["timestamp"],
            flow_rate=float(item["flow_rate"]),
            pressure=float(item["pressure"]),
            anomaly_label=item.get("anomaly_label", "normal"),
            processed=False,
        )
        for item in raw_items
    ]
    return readings, raw_items


def _mark_processed(readings_table, pipe_id: str, timestamp: str) -> None:
    """Update a Reading record to mark it as processed."""
    readings_table.update_item(
        Key={"pipe_id": pipe_id, "timestamp": timestamp},
        UpdateExpression="SET processed = :val",
        ExpressionAttributeValues={":val": True},
    )
