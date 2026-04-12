"""Impact simulator for AquaMind AI — pure computation, no external calls."""
from __future__ import annotations

import time
import uuid

from backend.app.models import IgnoreScenario, RepairScenario, SimulationResult

_SECONDS_PER_DAY = 86_400
_TTL_DAYS = 90


def compute_impact(
    alert_id: str,
    leak_rate: float,
    population_affected: int,
    repair_cost: float,
    time_horizon_days: int = 30,
) -> SimulationResult:
    """Compute the financial and infrastructure impact of ignoring vs. repairing a leak.

    Args:
        alert_id: Identifier of the alert being analysed.
        leak_rate: Leak rate in m³/h.
        population_affected: Number of people affected by the leak.
        repair_cost: Estimated repair cost in USD.
        time_horizon_days: Projection window in days (1–365, default 30).

    Returns:
        SimulationResult dataclass with both scenarios and a recommendation.

    Raises:
        ValueError: If time_horizon_days is outside [1, 365].
    """
    if not (1 <= time_horizon_days <= 365):
        raise ValueError("time_horizon_days must be between 1 and 365")

    # --- Ignore scenario ---
    total_water_loss_liters = leak_rate * time_horizon_days * 24 * 1000
    financial_cost_usd = (
        total_water_loss_liters * 0.001
        + population_affected * 0.5 * time_horizon_days
    )
    infrastructure_damage_score = min(
        1.0, (time_horizon_days / 365) * (leak_rate / 100)
    )

    ignore_scenario = IgnoreScenario(
        total_water_loss_liters=total_water_loss_liters,
        financial_cost_usd=financial_cost_usd,
        infrastructure_damage_score=infrastructure_damage_score,
    )

    # --- Repair scenario ---
    repair_scenario = RepairScenario(
        repair_cost_usd=repair_cost,
        water_loss_prevented_liters=total_water_loss_liters,
    )

    # --- Decision ---
    savings_usd = max(0.0, financial_cost_usd - repair_cost)
    recommended_action = (
        "Repair immediately" if savings_usd > 0 else "Monitor and reassess"
    )

    ttl = int(time.time()) + _TTL_DAYS * _SECONDS_PER_DAY

    return SimulationResult(
        simulation_id=str(uuid.uuid4()),
        alert_id=alert_id,
        ignore_scenario=ignore_scenario,
        repair_scenario=repair_scenario,
        savings_usd=savings_usd,
        recommended_action=recommended_action,
        ttl=ttl,
    )
