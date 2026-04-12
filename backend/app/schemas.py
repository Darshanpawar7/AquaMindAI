"""Pydantic request/response schemas for all API endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Standard response envelope
# ---------------------------------------------------------------------------

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Any


class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_message: str


# ---------------------------------------------------------------------------
# POST /simulate
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    num_pipes: int = Field(default=200, ge=1)
    num_junctions: int = Field(default=100, ge=1)
    days: int = Field(default=90, ge=1)
    interval_hours: int = Field(default=1, ge=1)
    anomaly_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    table_prefix: str = Field(default="aquamind")


class SimulateResponse(BaseModel):
    simulation_id: str
    pipes_generated: int
    readings_generated: int
    anomalies_injected: int


# ---------------------------------------------------------------------------
# GET /pipes
# ---------------------------------------------------------------------------

class PipeSchema(BaseModel):
    pipe_id: str
    junction_start: str
    junction_end: str
    length_m: float
    diameter_mm: float
    age_years: float
    population_affected: int
    repair_cost_usd: float
    material: str


class PipesResponse(BaseModel):
    pipes: List[PipeSchema]
    continuation_token: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------

class AlertSchema(BaseModel):
    alert_id: str
    pipe_id: str
    timestamp: str
    anomaly_type: str
    anomaly_score: float
    failure_probability: float
    priority_score: int
    priority_level: str
    immediate_action_required: bool
    flow_rate: float
    pressure: float
    ttl: Optional[int] = None


class AlertsResponse(BaseModel):
    alerts: List[AlertSchema]
    continuation_token: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /detect
# ---------------------------------------------------------------------------

class ReadingSchema(BaseModel):
    pipe_id: str
    timestamp: str
    flow_rate: float
    pressure: float
    anomaly_label: str = "normal"


class DetectRequest(BaseModel):
    readings: List[ReadingSchema] = Field(..., min_length=1)


class DetectResponse(BaseModel):
    alerts_created: int
    alerts: List[AlertSchema]


# ---------------------------------------------------------------------------
# POST /whatif
# ---------------------------------------------------------------------------

class WhatIfRequest(BaseModel):
    alert_id: str
    leak_rate: float = Field(..., gt=0)
    population_affected: int = Field(..., ge=0)
    repair_cost: float = Field(..., ge=0)
    time_horizon_days: int = Field(default=30, ge=1, le=365)


class IgnoreScenarioSchema(BaseModel):
    total_water_loss_liters: float
    financial_cost_usd: float
    infrastructure_damage_score: float


class RepairScenarioSchema(BaseModel):
    repair_cost_usd: float
    water_loss_prevented_liters: float


class WhatIfResponse(BaseModel):
    simulation_id: str
    alert_id: str
    ignore_scenario: IgnoreScenarioSchema
    repair_scenario: RepairScenarioSchema
    savings_usd: float
    recommended_action: str


# ---------------------------------------------------------------------------
# POST /explain
# ---------------------------------------------------------------------------

class ExplainRequest(BaseModel):
    alert_id: str
    pipe_id: str
    loss_rate: float = Field(..., gt=0)
    population_affected: int = Field(..., ge=0)
    repair_cost: float = Field(..., ge=0)
    time_horizon_days: int = Field(default=30, ge=1, le=365)
    simulation_id: Optional[str] = None


class ExplainResponse(BaseModel):
    recommended_action: str
    savings_usd: float
    repair_cost_usd: float
    urgency_rationale: str
    ai_text: str = ""
