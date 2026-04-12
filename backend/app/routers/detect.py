"""POST /detect endpoint — run anomaly detection on submitted sensor readings."""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.db import put_item_with_retry
from backend.app.models import Alert, Reading
from backend.app.responses import error_response, success_response

logger = __import__("logging").getLogger(__name__)
from backend.app.schemas import DetectRequest
from backend.models import anomaly_model
from backend.models.anomaly_model import ModelNotAvailableError
from backend.models.priority_scorer import assign_priority_level, compute_priority_score
from backend.models.risk_predictor import predict_failure_probability

router = APIRouter()

_ANOMALY_THRESHOLD = 0.5
_TTL_DAYS = 90
_SECONDS_PER_DAY = 86_400


@router.post("/detect")
def detect(request: DetectRequest) -> dict:
    """Run anomaly detection on a batch of sensor readings and persist alerts."""
    table_prefix = os.environ.get("TABLE_PREFIX", "aquamind")
    alerts_table_name = f"{table_prefix}-Alerts"

    # Convert schema readings to model Reading objects
    readings = [
        Reading(
            pipe_id=r.pipe_id,
            timestamp=r.timestamp,
            flow_rate=r.flow_rate,
            pressure=r.pressure,
            anomaly_label=r.anomaly_label,
        )
        for r in request.readings
    ]

    # Run anomaly detection — 503 if model unavailable
    try:
        scores = anomaly_model.predict(readings)
    except ModelNotAvailableError as exc:
        return JSONResponse(
            status_code=503,
            content=error_response(f"Model not available: {exc}"),
        )

    dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    alerts_table = dynamodb.Table(alerts_table_name)

    ttl = int(time.time()) + _TTL_DAYS * _SECONDS_PER_DAY
    created_alerts = []

    for reading, score in zip(readings, scores):
        if score <= _ANOMALY_THRESHOLD:
            continue

        # Risk prediction
        risk_result = predict_failure_probability(
            alert_frequency_7d=None,
            anomaly_severity_avg=score,
            pipe_age_years=None,
        )
        failure_prob = risk_result["failure_probability"]

        # Priority scoring (normalize population/cost to [0,1] — use score as proxy)
        priority_score = compute_priority_score(
            anomaly_score=score,
            population_factor=score,   # proxy when pipe metadata not available
            repair_cost_factor=score,  # proxy when pipe metadata not available
        )
        priority_level = assign_priority_level(failure_prob)
        immediate_action = priority_level == "Critical"

        alert = Alert(
            alert_id=str(uuid.uuid4()),
            pipe_id=reading.pipe_id,
            timestamp=reading.timestamp,
            anomaly_type=reading.anomaly_label if reading.anomaly_label != "normal" else "noise",
            anomaly_score=score,
            failure_probability=failure_prob,
            priority_score=priority_score,
            priority_level=priority_level,
            immediate_action_required=immediate_action,
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
        try:
            put_item_with_retry(alerts_table, item)
        except Exception as ddb_exc:
            logger.warning("DynamoDB write failed, saving to local store: %s", ddb_exc)
            from backend.app import local_store
            local_store.add_alert(item)
        created_alerts.append(item)

    return success_response({
        "alerts_created": len(created_alerts),
        "alerts": created_alerts,
    })
