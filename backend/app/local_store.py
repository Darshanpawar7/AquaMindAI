"""In-memory local store for development without AWS credentials.

Used automatically when DynamoDB is unavailable (no credentials / no network).
Data lives only for the lifetime of the uvicorn process.
"""
from __future__ import annotations

from typing import Dict, List

# pipe_id -> pipe dict
_pipes: Dict[str, dict] = {}

# alert_id -> alert dict
_alerts: Dict[str, dict] = {}

# simulation_id -> simulation result dict
_simulation_results: Dict[str, dict] = {}


# ── Pipes ──────────────────────────────────────────────────────────────────

def set_pipes(pipes: List[dict]) -> None:
    _pipes.clear()
    for p in pipes:
        _pipes[p["pipe_id"]] = p


def get_pipes() -> List[dict]:
    return list(_pipes.values())


def get_pipe(pipe_id: str) -> dict | None:
    return _pipes.get(pipe_id)


# ── Alerts ─────────────────────────────────────────────────────────────────

def add_alert(alert: dict) -> None:
    _alerts[alert["alert_id"]] = alert


def get_alerts() -> List[dict]:
    return list(_alerts.values())


def get_alert(alert_id: str) -> dict | None:
    return _alerts.get(alert_id)


# ── Simulation Results ─────────────────────────────────────────────────────

def add_simulation_result(result: dict) -> None:
    _simulation_results[result["simulation_id"]] = result


def get_simulation_result(simulation_id: str) -> dict | None:
    return _simulation_results.get(simulation_id)


def clear() -> None:
    _pipes.clear()
    _alerts.clear()
    _simulation_results.clear()
