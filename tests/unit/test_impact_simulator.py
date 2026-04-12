"""Unit tests for backend/app/simulator.py — compute_impact()."""
from __future__ import annotations

import time

import pytest

from backend.app.simulator import compute_impact


# ---------------------------------------------------------------------------
# Known-value tests
# ---------------------------------------------------------------------------

def test_water_loss_calculation():
    """total_water_loss_liters = leak_rate * days * 24 * 1000."""
    result = compute_impact(
        alert_id="alert-001",
        leak_rate=2.0,
        population_affected=0,
        repair_cost=0.0,
        time_horizon_days=10,
    )
    expected = 2.0 * 10 * 24 * 1000  # 480_000
    assert result.ignore_scenario.total_water_loss_liters == pytest.approx(expected)


def test_financial_cost_calculation():
    """financial_cost_usd = water_loss * 0.001 + population * 0.5 * days."""
    result = compute_impact(
        alert_id="alert-002",
        leak_rate=1.0,
        population_affected=100,
        repair_cost=0.0,
        time_horizon_days=30,
    )
    water_loss = 1.0 * 30 * 24 * 1000  # 720_000
    expected_cost = water_loss * 0.001 + 100 * 0.5 * 30  # 720 + 1500 = 2220
    assert result.ignore_scenario.financial_cost_usd == pytest.approx(expected_cost)


def test_infrastructure_damage_score_capped_at_one():
    """infrastructure_damage_score must not exceed 1.0."""
    result = compute_impact(
        alert_id="alert-003",
        leak_rate=1000.0,  # very high leak rate
        population_affected=0,
        repair_cost=0.0,
        time_horizon_days=365,
    )
    assert result.ignore_scenario.infrastructure_damage_score <= 1.0


def test_infrastructure_damage_score_formula():
    """infrastructure_damage_score = min(1.0, (days/365) * (leak_rate/100))."""
    result = compute_impact(
        alert_id="alert-004",
        leak_rate=50.0,
        population_affected=0,
        repair_cost=0.0,
        time_horizon_days=73,
    )
    expected = min(1.0, (73 / 365) * (50.0 / 100))
    assert result.ignore_scenario.infrastructure_damage_score == pytest.approx(expected)


def test_savings_usd_positive_when_repair_cheaper():
    """savings_usd = financial_cost - repair_cost when positive."""
    result = compute_impact(
        alert_id="alert-005",
        leak_rate=5.0,
        population_affected=500,
        repair_cost=100.0,
        time_horizon_days=30,
    )
    water_loss = 5.0 * 30 * 24 * 1000
    financial_cost = water_loss * 0.001 + 500 * 0.5 * 30
    expected_savings = max(0.0, financial_cost - 100.0)
    assert result.savings_usd == pytest.approx(expected_savings)
    assert result.savings_usd > 0


def test_repair_scenario_values():
    """repair_cost_usd and water_loss_prevented_liters are set correctly."""
    result = compute_impact(
        alert_id="alert-006",
        leak_rate=3.0,
        population_affected=200,
        repair_cost=5000.0,
        time_horizon_days=20,
    )
    expected_water_loss = 3.0 * 20 * 24 * 1000
    assert result.repair_scenario.repair_cost_usd == pytest.approx(5000.0)
    assert result.repair_scenario.water_loss_prevented_liters == pytest.approx(
        expected_water_loss
    )


# ---------------------------------------------------------------------------
# savings_usd is never negative
# ---------------------------------------------------------------------------

def test_savings_usd_never_negative_when_repair_expensive():
    """savings_usd must be 0.0 when repair cost exceeds financial cost."""
    result = compute_impact(
        alert_id="alert-007",
        leak_rate=0.001,
        population_affected=0,
        repair_cost=1_000_000.0,
        time_horizon_days=1,
    )
    assert result.savings_usd >= 0.0


def test_savings_usd_never_negative_zero_leak():
    """savings_usd must be 0.0 when there is no financial benefit."""
    result = compute_impact(
        alert_id="alert-008",
        leak_rate=0.0,
        population_affected=0,
        repair_cost=999.0,
        time_horizon_days=1,
    )
    assert result.savings_usd == 0.0


# ---------------------------------------------------------------------------
# Recommended action
# ---------------------------------------------------------------------------

def test_recommended_action_repair_when_savings_positive():
    result = compute_impact(
        alert_id="alert-009",
        leak_rate=10.0,
        population_affected=1000,
        repair_cost=1.0,
        time_horizon_days=30,
    )
    assert result.recommended_action == "Repair immediately"


def test_recommended_action_monitor_when_no_savings():
    result = compute_impact(
        alert_id="alert-010",
        leak_rate=0.0,
        population_affected=0,
        repair_cost=1_000_000.0,
        time_horizon_days=1,
    )
    assert result.recommended_action == "Monitor and reassess"


# ---------------------------------------------------------------------------
# Boundary validation for time_horizon_days
# ---------------------------------------------------------------------------

def test_time_horizon_zero_raises():
    with pytest.raises(ValueError, match="time_horizon_days must be between 1 and 365"):
        compute_impact("a", 1.0, 0, 0.0, time_horizon_days=0)


def test_time_horizon_366_raises():
    with pytest.raises(ValueError, match="time_horizon_days must be between 1 and 365"):
        compute_impact("a", 1.0, 0, 0.0, time_horizon_days=366)


def test_time_horizon_1_is_valid():
    result = compute_impact("a", 1.0, 0, 0.0, time_horizon_days=1)
    assert result is not None


def test_time_horizon_365_is_valid():
    result = compute_impact("a", 1.0, 0, 0.0, time_horizon_days=365)
    assert result is not None


# ---------------------------------------------------------------------------
# simulation_id and ttl
# ---------------------------------------------------------------------------

def test_simulation_id_is_non_empty_string():
    result = compute_impact("alert-id", 1.0, 10, 100.0)
    assert isinstance(result.simulation_id, str)
    assert len(result.simulation_id) > 0


def test_simulation_id_is_unique():
    r1 = compute_impact("alert-id", 1.0, 10, 100.0)
    r2 = compute_impact("alert-id", 1.0, 10, 100.0)
    assert r1.simulation_id != r2.simulation_id


def test_ttl_is_set():
    before = int(time.time())
    result = compute_impact("alert-id", 1.0, 10, 100.0)
    after = int(time.time())

    assert result.ttl is not None
    # TTL should be ~90 days from now
    assert result.ttl > before + 89 * 86_400
    assert result.ttl < after + 91 * 86_400


def test_alert_id_preserved():
    result = compute_impact("my-alert-xyz", 1.0, 0, 0.0)
    assert result.alert_id == "my-alert-xyz"
