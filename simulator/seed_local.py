"""Seed the local AquaMind AI backend with EPANET-like simulation data.

Generates a realistic water network (pipes, junctions) with 90-day sensor
readings and injected anomalies, then POSTs everything to the running
backend's /seed endpoint so the dashboard has live data to display.

Usage:
    python simulator/seed_local.py [--api-url http://localhost:8000]
"""
from __future__ import annotations

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from dataclasses import asdict

from simulator.generate import generate_network, generate_readings, inject_anomalies

# ── EPANET-like network parameters ────────────────────────────────────────
NUM_PIPES = 30        # keep small for fast local demo
NUM_JUNCTIONS = 20
DAYS = 7              # 7 days of hourly readings
INTERVAL_HOURS = 1
MIN_ANOMALIES = 20    # ensure plenty of alerts


def main(api_url: str = "http://localhost:8000") -> None:
    print(f"==> Generating EPANET-like water network...")
    network = generate_network(num_pipes=NUM_PIPES, num_junctions=NUM_JUNCTIONS)
    print(f"    Pipes     : {len(network.pipes)}")
    print(f"    Junctions : {len(network.junctions)}")

    print(f"==> Generating {DAYS}-day sensor readings ({INTERVAL_HOURS}h interval)...")
    readings = generate_readings(network, days=DAYS, interval_hours=INTERVAL_HOURS)
    print(f"    Readings  : {len(readings)}")

    print(f"==> Injecting >={MIN_ANOMALIES} anomalies...")
    readings = inject_anomalies(readings, min_count=MIN_ANOMALIES)
    anomalous = [r for r in readings if r.anomaly_label != "normal"]
    print(f"    Anomalous : {len(anomalous)}")
    for atype in ("leak", "degradation", "noise"):
        n = sum(1 for r in anomalous if r.anomaly_label == atype)
        print(f"      {atype:<12}: {n}")

    # Build payload — only send anomalous readings to keep the POST small
    # (the detector only creates alerts for anomalous ones anyway)
    pipes_payload = [asdict(p) for p in network.pipes]
    readings_payload = [
        {
            "pipe_id": r.pipe_id,
            "timestamp": r.timestamp,
            "flow_rate": r.flow_rate,
            "pressure": r.pressure,
            "anomaly_label": r.anomaly_label,
        }
        for r in readings
        if r.anomaly_label != "normal"   # only anomalous readings → alerts
    ]

    print(f"\n==> POSTing to {api_url}/seed ...")
    try:
        resp = requests.post(
            f"{api_url}/seed",
            json={"pipes": pipes_payload, "readings": readings_payload},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        print(f"    Pipes loaded      : {data.get('pipes_loaded')}")
        print(f"    Readings processed: {data.get('readings_processed')}")
        print(f"    Alerts created    : {data.get('alerts_created')}")
        print("\n[OK] Dashboard is ready -- open http://localhost:3000")
    except requests.exceptions.ConnectionError:
        print(f"\n[ERR] Could not connect to {api_url}. Is the backend running?")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERR] Seed failed: {e}\n{resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed local AquaMind AI backend")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()
    main(args.api_url)
