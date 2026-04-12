# Backend + AI System

## Requirements
Build a FastAPI backend deployed on AWS Lambda.

## Endpoints
- POST /simulate → generate synthetic data
- GET /pipes → list pipes with metadata
- GET /alerts → return alerts with priority scores
- POST /detect → run anomaly detection
- POST /whatif → Impact Simulator (ignore vs repair)
- POST /explain → AI recommendation (Bedrock)

## AI Models

### 1. Anomaly Detection
- Model: Isolation Forest
- Input: flow, pressure
- Output: anomaly_score (0–1)

### 2. Priority Scoring
priority_score = (anomaly_score * 0.5) + (population_factor * 0.3) + (repair_cost_factor * 0.2)

- Normalize all factors between 0 and 1
- Output: HIGH / MEDIUM / LOW priority

### 3. Risk Prediction
- Simple regression model
- Predict failure probability (next 7 days)

## Impact Simulator (Key Feature)
Input:
- leak_rate (liters/hour)
- population_affected
- repair_cost

Output:
- total_loss_if_ignored
- cost_of_repair
- savings
- recommended_action

## Bedrock Integration
Prompt template:

"Given a leak in pipe {pipe_id}, loss rate {loss_rate}, population affected {population}, and repair cost {repair_cost}, calculate the impact of ignoring vs repairing. Return recommendation with savings."

## Output Example
{
  "pipe_id": "P12",
  "priority": "HIGH",
  "loss_if_ignored": 12000,
  "repair_cost": 8500,
  "savings": 3500,
  "recommendation": "Repair within 6 hours"
}

## Tests
- API response validation
- Priority score correctness
- Impact simulation accuracy
- Mock Bedrock responses