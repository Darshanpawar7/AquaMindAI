"""POST /seed — load local EPANET simulation data into the in-memory store.

Only active in local/dev mode (when DynamoDB is unavailable).
Accepts pipes and sensor readings, runs anomaly detection, and populates
the local store so the dashboard has data to display.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app import local_store
from backend.app.models import Alert, Reading
from backend.app.responses import success_response
from backend.models import anomaly_model
from backend.models.anomaly_model import ModelNotAvailableError
from backend.models.priority_scorer import assign_priority_level, compute_priority_score
from backend.models.risk_predictor import predict_failure_probability

logger = logging.getLogger(__name__)
router = APIRouter()

_ANOMALY_THRESHOLD = 0.5
_TTL_DAYS = 90


class PipePayload(BaseModel):
    pipe_id: str
    junction_start: str
    junction_end: str
    length_m: float
    diameter_mm: float
    age_years: float
    population_affected: int
    repair_cost_usd: float
    material: str


class ReadingPayload(BaseModel):
    pipe_id: str
    timestamp: str
    flow_rate: float
    pressure: float
    anomaly_label: str = "normal"


class SeedRequest(BaseModel):
    pipes: List[PipePayload]
    readings: List[ReadingPayload]


@router.post("/seed")
def seed(request: SeedRequest) -> dict:
    """Populate the local in-memory store with pipes and detected alerts."""
    local_store.clear()

    # Store pipes
    pipes_data = [p.model_dump() for p in request.pipes]
    local_store.set_pipes(pipes_data)

    # Run anomaly detection on readings
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

    try:
        scores = anomaly_model.predict(readings)
    except ModelNotAvailableError:
        logger.warning("Model unavailable during seed — using anomaly_label as fallback")
        scores = [0.8 if r.anomaly_label != "normal" else 0.1 for r in readings]

    ttl = int(time.time()) + _TTL_DAYS * 86_400
    alerts_created = 0

    for reading, score in zip(readings, scores):
        if score <= _ANOMALY_THRESHOLD:
            continue

        risk = predict_failure_probability(
            alert_frequency_7d=None,
            anomaly_severity_avg=score,
            pipe_age_years=None,
        )
        failure_prob = risk["failure_probability"]
        priority_score = compute_priority_score(score, score, score)
        priority_level = assign_priority_level(failure_prob)

        alert = {
            "alert_id": str(uuid.uuid4()),
            "pipe_id": reading.pipe_id,
            "timestamp": reading.timestamp,
            "anomaly_type": reading.anomaly_label if reading.anomaly_label != "normal" else "noise",
            "anomaly_score": score,
            "failure_probability": failure_prob,
            "priority_score": priority_score,
            "priority_level": priority_level,
            "immediate_action_required": priority_level == "Critical",
            "flow_rate": reading.flow_rate,
            "pressure": reading.pressure,
            "ttl": ttl,
        }
        local_store.add_alert(alert)
        alerts_created += 1

    return success_response({
        "pipes_loaded": len(pipes_data),
        "readings_processed": len(readings),
        "alerts_created": alerts_created,
    })
