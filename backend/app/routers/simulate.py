"""POST /simulate endpoint — trigger a simulation run."""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter

from backend.app.responses import success_response
from backend.app.schemas import SimulateRequest
from simulator.generate import generate_network, generate_readings, inject_anomalies
from simulator.upload import upload_to_dynamodb

router = APIRouter()


@router.post("/simulate")
def simulate(request: SimulateRequest) -> dict:
    """Generate a synthetic water network, inject anomalies, and upload to DynamoDB."""
    simulation_id = str(uuid.uuid4())
    table_prefix = os.environ.get("TABLE_PREFIX", request.table_prefix)

    network = generate_network(
        num_pipes=request.num_pipes,
        num_junctions=request.num_junctions,
    )
    readings = generate_readings(
        network,
        days=request.days,
        interval_hours=request.interval_hours,
    )
    readings = inject_anomalies(readings, min_count=max(10, int(len(readings) * request.anomaly_rate)))

    anomalies_injected = sum(1 for r in readings if r.anomaly_label != "normal")

    upload_to_dynamodb(readings, network.pipes, table_prefix=table_prefix)

    return success_response({
        "simulation_id": simulation_id,
        "pipes_generated": len(network.pipes),
        "readings_generated": len(readings),
        "anomalies_injected": anomalies_injected,
    })
