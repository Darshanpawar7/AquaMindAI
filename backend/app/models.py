"""Core data models for AquaMind AI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Pipe:
    pipe_id: str
    junction_start: str
    junction_end: str
    length_m: float
    diameter_mm: float
    age_years: float
    population_affected: int
    repair_cost_usd: float
    material: str


@dataclass
class Network:
    pipes: List[Pipe] = field(default_factory=list)
    junctions: List[str] = field(default_factory=list)


@dataclass
class Reading:
    pipe_id: str
    timestamp: str  # ISO 8601
    flow_rate: float  # m³/h
    pressure: float  # psi
    anomaly_label: str  # "normal", "leak", "degradation", "noise"
    processed: bool = False
    ttl: Optional[int] = None  # Unix epoch


@dataclass
class Alert:
    alert_id: str
    pipe_id: str
    timestamp: str  # ISO 8601
    anomaly_type: str  # "leak", "degradation", "noise"
    anomaly_score: float  # 0.0–1.0
    failure_probability: float  # 0.0–1.0
    priority_score: int  # 1–100
    priority_level: str  # "Critical", "High", "Medium", "Low"
    immediate_action_required: bool
    flow_rate: float
    pressure: float
    ttl: Optional[int] = None  # Unix epoch


@dataclass
class IgnoreScenario:
    total_water_loss_liters: float
    financial_cost_usd: float
    infrastructure_damage_score: float


@dataclass
class RepairScenario:
    repair_cost_usd: float
    water_loss_prevented_liters: float


@dataclass
class SimulationResult:
    simulation_id: str
    alert_id: str
    ignore_scenario: IgnoreScenario
    repair_scenario: RepairScenario
    savings_usd: float
    recommended_action: str
    ai_recommendation: str = ""
    ttl: Optional[int] = None  # Unix epoch


@dataclass
class RecommendationResponse:
    recommended_action: str
    savings_usd: float
    repair_cost_usd: float
    urgency_rationale: str
    ai_text: str = ""
