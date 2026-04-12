"""DynamoDB upload script for AquaMind AI.

Uploads generated Pipe and Reading records to DynamoDB using boto3 batch_writer.
Supports a DRY_RUN mode (set DRY_RUN=true) that skips actual DynamoDB calls.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import asdict
from decimal import Decimal
from typing import List

# Allow running as a script from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.models import Pipe, Reading

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

_TTL_90_DAYS = 90 * 24 * 3600  # seconds


def _to_dynamo_item(obj: object) -> dict:
    """Convert a dataclass to a DynamoDB-compatible dict (floats → Decimal)."""
    raw = asdict(obj)  # type: ignore[arg-type]
    return {k: Decimal(str(v)) if isinstance(v, float) else v for k, v in raw.items()}


def upload_to_dynamodb(
    readings: List[Reading],
    pipes: List[Pipe],
    table_prefix: str = "aquamind",
) -> dict:
    """Upload Pipe and Reading records to DynamoDB.

    For each Reading:
      - Sets ``ttl`` to Unix epoch now + 90 days (overrides any existing value).
      - Sets ``processed`` to False.

    For each Pipe:
      - Writes all metadata fields as-is.

    Uses boto3 ``batch_writer`` for efficient batching (up to 25 items/request).
    Per-record errors are logged and the upload continues; a summary is returned.

    Args:
        readings: List of Reading dataclass instances to upload.
        pipes: List of Pipe dataclass instances to upload.
        table_prefix: Prefix for DynamoDB table names (default ``"aquamind"``).
                      Tables used: ``{table_prefix}-Pipes``, ``{table_prefix}-Readings``.

    Returns:
        A dict with keys ``pipes_uploaded``, ``readings_uploaded``, and ``errors``.
    """
    dry_run = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

    pipes_table_name = f"{table_prefix}-Pipes"
    readings_table_name = f"{table_prefix}-Readings"

    pipes_uploaded = 0
    readings_uploaded = 0
    errors = 0

    ttl_value = int(time.time()) + _TTL_90_DAYS

    if dry_run:
        logger.info("[DRY RUN] Skipping DynamoDB calls.")
        logger.info(
            "[DRY RUN] Would upload %d pipes to '%s'.", len(pipes), pipes_table_name
        )
        logger.info(
            "[DRY RUN] Would upload %d readings to '%s'.",
            len(readings),
            readings_table_name,
        )
        return {
            "pipes_uploaded": len(pipes),
            "readings_uploaded": len(readings),
            "errors": 0,
        }

    import boto3  # imported lazily so dry-run works without AWS credentials

    dynamodb = boto3.resource("dynamodb")
    pipes_table = dynamodb.Table(pipes_table_name)
    readings_table = dynamodb.Table(readings_table_name)

    # --- Upload Pipes ---
    logger.info("Uploading %d pipes to '%s'…", len(pipes), pipes_table_name)
    with pipes_table.batch_writer() as batch:
        for pipe in pipes:
            try:
                item = _to_dynamo_item(pipe)
                batch.put_item(Item=item)
                pipes_uploaded += 1
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to upload pipe '%s': %s", pipe.pipe_id, exc
                )
                errors += 1

    # --- Upload Readings ---
    logger.info(
        "Uploading %d readings to '%s'…", len(readings), readings_table_name
    )
    with readings_table.batch_writer() as batch:
        for reading in readings:
            try:
                item = _to_dynamo_item(reading)
                item["ttl"] = ttl_value
                item["processed"] = False
                batch.put_item(Item=item)
                readings_uploaded += 1
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to upload reading pipe_id='%s' timestamp='%s': %s",
                    reading.pipe_id,
                    reading.timestamp,
                    exc,
                )
                errors += 1

    summary = {
        "pipes_uploaded": pipes_uploaded,
        "readings_uploaded": readings_uploaded,
        "errors": errors,
    }
    logger.info("Upload complete: %s", summary)
    return summary


# ---------------------------------------------------------------------------
# Script entry-point — generates a small network and prints the upload summary
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from simulator.generate import generate_network, generate_readings, inject_anomalies

    print("Generating small network (5 pipes, 1 day)…")
    network = generate_network(num_pipes=5, num_junctions=10)
    readings = generate_readings(network, days=1, interval_hours=1)
    readings = inject_anomalies(readings, min_count=5)

    print(f"  Pipes    : {len(network.pipes)}")
    print(f"  Readings : {len(readings)}")

    summary = upload_to_dynamodb(readings, network.pipes, table_prefix="aquamind")
    print("\nUpload summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
