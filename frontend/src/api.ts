import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const client = axios.create({ baseURL: BASE_URL });

// --- Interfaces ---

export interface Alert {
  alert_id: string;
  pipe_id: string;
  timestamp: string;
  anomaly_type: string;
  anomaly_score: number;
  failure_probability: number;
  priority_score: number;
  priority_level: 'Critical' | 'High' | 'Medium' | 'Low';
  immediate_action_required: boolean;
  flow_rate: number;
  pressure: number;
}

export interface Pipe {
  pipe_id: string;
  junction_start: string;
  junction_end: string;
  length_m: number;
  diameter_mm: number;
  age_years: number;
  population_affected: number;
  repair_cost_usd: number;
  material: string;
}

export interface SimulationResult {
  ignore_scenario: {
    total_water_loss_liters: number;
    financial_cost_usd: number;
    infrastructure_damage_score: number;
  };
  repair_scenario: {
    repair_cost_usd: number;
    water_loss_prevented_liters: number;
  };
  savings_usd: number;
  recommended_action: string;
}

export interface RecommendationResult {
  recommended_action: string;
  savings_usd: number;
  repair_cost_usd: number;
  urgency_rationale: string;
}

// --- Request payload types ---

export interface ReadingPayload {
  pipe_id: string;
  timestamp: string;
  flow_rate: number;
  pressure: number;
}

export interface WhatIfPayload {
  alert_id: string;
  leak_rate: number;
  population_affected: number;
  repair_cost: number;
  time_horizon_days?: number;
}

export interface ExplainPayload {
  alert_id: string;
  pipe_id: string;
  loss_rate: number;
  population_affected: number;
  repair_cost: number;
  time_horizon_days: number;
}

export interface SimulatePayload {
  num_pipes?: number;
  num_junctions?: number;
  days?: number;
}

// --- API functions ---

export async function getAlerts(continuationToken?: string): Promise<Alert[]> {
  const params = continuationToken ? { continuation_token: continuationToken } : {};
  const res = await client.get('/alerts', { params });
  return res.data.data?.alerts ?? res.data.data ?? [];
}

export async function getPipes(continuationToken?: string): Promise<Pipe[]> {
  const params = continuationToken ? { continuation_token: continuationToken } : {};
  const res = await client.get('/pipes', { params });
  return res.data.data?.pipes ?? res.data.data ?? [];
}

export async function runDetect(readings: ReadingPayload[]): Promise<Alert[]> {
  const res = await client.post('/detect', { readings });
  return res.data.data?.alerts ?? res.data.data ?? [];
}

export async function runWhatIf(payload: WhatIfPayload): Promise<SimulationResult> {
  const res = await client.post('/whatif', payload);
  return res.data.data;
}

export async function runExplain(payload: ExplainPayload): Promise<RecommendationResult> {
  const res = await client.post('/explain', payload);
  return res.data.data;
}

export async function runSimulate(payload: SimulatePayload): Promise<{ simulation_id: string }> {
  const res = await client.post('/simulate', payload);
  return res.data.data;
}
