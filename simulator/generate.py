"""Simulation engine for AquaMind AI.

Generates synthetic water network data (pipes, junctions, time-series readings)
using NumPy for realistic sensor values and Faker for pipe metadata.
"""
from __future__ import annotations

import copy
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
from faker import Faker

# Allow running as a script from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.models import Network, Pipe, Reading

fake = Faker()
rng = np.random.default_rng(seed=42)

MATERIALS = ["PVC", "cast_iron", "steel", "HDPE"]


def generate_network(num_pipes: int = 200, num_junctions: int = 100) -> Network:
    """Generate a synthetic water network with pipes and junctions.

    Args:
        num_pipes: Number of pipes to generate (default 200).
        num_junctions: Number of junctions to generate (default 100).

    Returns:
        A Network instance populated with Pipe objects and junction IDs.
    """
    junctions = [f"J{i:03d}" for i in range(num_junctions)]

    pipes: List[Pipe] = []
    for i in range(num_pipes):
        j_start, j_end = rng.choice(num_junctions, size=2, replace=False)
        pipe = Pipe(
            pipe_id=f"pipe_{i:03d}",
            junction_start=junctions[j_start],
            junction_end=junctions[j_end],
            length_m=round(float(rng.uniform(50, 500)), 2),
            diameter_mm=float(rng.choice([100, 150, 200, 250, 300])),
            age_years=round(float(rng.uniform(1, 50)), 1),
            population_affected=int(rng.integers(100, 5000)),
            repair_cost_usd=round(float(rng.uniform(5_000, 50_000)), 2),
            material=str(rng.choice(MATERIALS)),
        )
        pipes.append(pipe)

    return Network(pipes=pipes, junctions=junctions)


def generate_readings(
    network: Network,
    days: int = 90,
    interval_hours: int = 1,
) -> List[Reading]:
    """Generate normal (non-anomalous) time-series readings for every pipe.

    Each reading has:
        - pipe_id
        - timestamp (ISO 8601, UTC)
        - flow_rate  ~50–200 m³/h with Gaussian noise
        - pressure   ~40–80 psi with Gaussian noise
        - anomaly_label = "normal"

    Args:
        network: The Network whose pipes will receive readings.
        days: Number of days of history to generate (default 90).
        interval_hours: Hours between consecutive readings (default 1).

    Returns:
        A flat list of Reading objects ordered by pipe then timestamp.
    """
    steps = (days * 24) // interval_hours
    start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    readings: List[Reading] = []

    for pipe in network.pipes:
        # Per-pipe baseline drawn once so each pipe has its own "normal" range
        base_flow = float(rng.uniform(50, 200))
        base_pressure = float(rng.uniform(40, 80))

        # Vectorised noise generation for the whole time-series
        flow_noise = rng.normal(0, base_flow * 0.05, size=steps)
        pressure_noise = rng.normal(0, base_pressure * 0.03, size=steps)

        for step in range(steps):
            ts = start_time + timedelta(hours=step * interval_hours)
            flow = max(0.0, round(base_flow + float(flow_noise[step]), 4))
            pressure = max(0.0, round(base_pressure + float(pressure_noise[step]), 4))

            readings.append(
                Reading(
                    pipe_id=pipe.pipe_id,
                    timestamp=ts.isoformat(),
                    flow_rate=flow,
                    pressure=pressure,
                    anomaly_label="normal",
                )
            )

    return readings


def inject_anomalies(readings: List[Reading], min_count: int = 10) -> List[Reading]:
    """Inject anomalies into a list of readings by mutating copies of selected readings.

    Three anomaly types are injected:
        - "leak"        : pressure drop (30–60%) + flow spike (50–150%)
        - "degradation" : gradual pressure decline over 3–8 consecutive steps (5–15% per step)
        - "noise"       : random large spike in both flow and pressure (±50–100% of baseline)

    The ``anomaly_label`` field of each mutated reading is set to the anomaly type.
    Normal readings are preserved; anomalous copies replace the originals at the
    selected indices.

    Args:
        readings: Flat list of Reading objects (typically from generate_readings).
        min_count: Minimum total number of anomalies to inject (default 10).

    Returns:
        The full list of readings with anomalies injected in-place (copies replace
        originals at selected positions).
    """
    if not readings:
        return readings

    # Build a mapping from pipe_id → list of indices in `readings`
    pipe_index_map: dict[str, List[int]] = {}
    for idx, r in enumerate(readings):
        pipe_index_map.setdefault(r.pipe_id, []).append(idx)

    pipe_ids = list(pipe_index_map.keys())
    result = list(readings)  # shallow copy of the list; we'll replace elements

    injected = 0
    anomaly_types = ["leak", "degradation", "noise"]

    # Keep injecting rounds until we reach min_count
    while injected < min_count:
        # Pick a random anomaly type
        atype = str(rng.choice(anomaly_types))

        # Pick a random pipe that has enough readings
        eligible = [p for p in pipe_ids if len(pipe_index_map[p]) >= 8]
        if not eligible:
            eligible = pipe_ids
        pipe_id = str(rng.choice(eligible))
        indices = pipe_index_map[pipe_id]

        if atype == "leak":
            # Single reading: pressure drop + flow spike
            idx = int(rng.choice(indices))
            original = result[idx]
            mutated = copy.copy(original)
            drop_factor = float(rng.uniform(0.30, 0.60))
            spike_factor = float(rng.uniform(0.50, 1.50))
            mutated.pressure = round(original.pressure * (1.0 - drop_factor), 4)
            mutated.flow_rate = round(original.flow_rate * (1.0 + spike_factor), 4)
            mutated.anomaly_label = "leak"
            result[idx] = mutated
            injected += 1

        elif atype == "degradation":
            # Sequence of 3–8 consecutive readings with gradual pressure decline
            steps = int(rng.integers(3, 9))  # 3 to 8 inclusive
            if len(indices) < steps:
                steps = len(indices)
            start_pos = int(rng.integers(0, len(indices) - steps + 1))
            seq_indices = indices[start_pos : start_pos + steps]
            for step_num, idx in enumerate(seq_indices):
                original = result[idx]
                mutated = copy.copy(original)
                per_step_drop = float(rng.uniform(0.05, 0.15))
                cumulative_drop = per_step_drop * (step_num + 1)
                mutated.pressure = round(
                    max(0.0, original.pressure * (1.0 - cumulative_drop)), 4
                )
                mutated.anomaly_label = "degradation"
                result[idx] = mutated
            injected += steps

        else:  # noise
            # Single reading: large random spike in both flow and pressure
            idx = int(rng.choice(indices))
            original = result[idx]
            mutated = copy.copy(original)
            flow_spike = float(rng.uniform(0.50, 1.00))
            pressure_spike = float(rng.uniform(0.50, 1.00))
            # Randomly add or subtract
            flow_sign = 1.0 if rng.random() > 0.5 else -1.0
            pressure_sign = 1.0 if rng.random() > 0.5 else -1.0
            mutated.flow_rate = round(
                max(0.0, original.flow_rate * (1.0 + flow_sign * flow_spike)), 4
            )
            mutated.pressure = round(
                max(0.0, original.pressure * (1.0 + pressure_sign * pressure_spike)), 4
            )
            mutated.anomaly_label = "noise"
            result[idx] = mutated
            injected += 1

    return result


# ---------------------------------------------------------------------------
# Script entry-point — quick smoke test with a small network
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating test network (5 pipes, 10 junctions, 3 days @ 1h)…")
    net = generate_network(num_pipes=5, num_junctions=10)
    print(f"  Pipes    : {len(net.pipes)}")
    print(f"  Junctions: {len(net.junctions)}")

    readings = generate_readings(net, days=3, interval_hours=1)
    print(f"  Readings : {len(readings)}")

    # Show a sample reading
    sample = readings[0]
    print(f"\nSample reading:")
    print(f"  pipe_id       : {sample.pipe_id}")
    print(f"  timestamp     : {sample.timestamp}")
    print(f"  flow_rate     : {sample.flow_rate} m³/h")
    print(f"  pressure      : {sample.pressure} psi")
    print(f"  anomaly_label : {sample.anomaly_label}")

    # Basic assertions
    expected_readings = 5 * 3 * 24  # pipes × days × hours
    assert len(readings) == expected_readings, (
        f"Expected {expected_readings} readings, got {len(readings)}"
    )
    assert all(r.anomaly_label == "normal" for r in readings)
    assert all(r.flow_rate >= 0 for r in readings)
    assert all(r.pressure >= 0 for r in readings)

    print("\nInjecting anomalies…")
    readings_with_anomalies = inject_anomalies(readings, min_count=10)
    anomalous = [r for r in readings_with_anomalies if r.anomaly_label != "normal"]
    print(f"  Total readings  : {len(readings_with_anomalies)}")
    print(f"  Anomalous       : {len(anomalous)}")

    # Count by type
    for atype in ("leak", "degradation", "noise"):
        count = sum(1 for r in anomalous if r.anomaly_label == atype)
        print(f"    {atype:<12}: {count}")

    # Show a sample anomalous reading
    if anomalous:
        sample_a = anomalous[0]
        print(f"\nSample anomalous reading:")
        print(f"  pipe_id       : {sample_a.pipe_id}")
        print(f"  timestamp     : {sample_a.timestamp}")
        print(f"  flow_rate     : {sample_a.flow_rate} m³/h")
        print(f"  pressure      : {sample_a.pressure} psi")
        print(f"  anomaly_label : {sample_a.anomaly_label}")

    # Verify anomaly injection
    assert len(readings_with_anomalies) == expected_readings, (
        "inject_anomalies must not change the total number of readings"
    )
    assert len(anomalous) >= 10, (
        f"Expected at least 10 anomalies, got {len(anomalous)}"
    )
    assert all(r.flow_rate >= 0 for r in readings_with_anomalies)
    assert all(r.pressure >= 0 for r in readings_with_anomalies)
    assert all(
        r.anomaly_label in ("normal", "leak", "degradation", "noise")
        for r in readings_with_anomalies
    )

    print("\nAll assertions passed.")
