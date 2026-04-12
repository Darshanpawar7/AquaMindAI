# Implementation Plan: AquaMind AI

## Overview

Incremental implementation of the AquaMind AI platform: simulation engine → ML models → FastAPI backend → Anomaly Detector Lambda → Impact Simulator → Recommendation Engine → DynamoDB data layer → React Dashboard → AWS SAM infrastructure → tests.

Each task builds on the previous, ending with all components wired together and validated.

## Tasks

- [x] 1. Project scaffolding and core interfaces
  - Create directory structure: `simulator/`, `backend/app/`, `backend/detector/`, `backend/models/`, `frontend/src/`, `tests/unit/`, `tests/property/`, `tests/frontend/`, `infra/`
  - Define Python dataclasses/TypedDicts for `Network`, `Reading`, `Alert`, `SimulationResult`, `RecommendationResponse` in `backend/app/models.py`
  - Define Pydantic request/response schemas for all API endpoints in `backend/app/schemas.py`
  - Set up `requirements.txt` (fastapi, mangum, boto3, scikit-learn, numpy, faker, hypothesis) and `frontend/package.json` (react, typescript, fast-check)
  - _Requirements: 1.1, 8.1, 8.2_

- [ ] 2. Simulation engine
  - [x] 2.1 Implement network and readings generator
    - Write `simulator/generate.py` with `generate_network(num_pipes=200, num_junctions=100)` and `generate_readings(network, days=90, interval_hours=1)`
    - Produce flow rate (m³/h) and pressure (psi) time-series for each pipe using NumPy; attach `pipe_id`, `timestamp`, `anomaly_label="normal"`
    - _Requirements: 1.1_

  - [ ]* 2.2 Write property test for simulation coverage (Property 1)
    - **Property 1: Simulation produces readings for all nodes**
    - **Validates: Requirements 1.1**
    - Tag: `# Feature: aquamind-ai, Property 1`
    - File: `tests/property/test_props_simulation.py`

  - [x] 2.3 Implement anomaly injection
    - Write `inject_anomalies(readings, min_count=10)` in `simulator/generate.py`
    - Inject leak (pressure drop + flow spike), gradual degradation, and random noise anomaly types; set `anomaly_label` accordingly
    - _Requirements: 1.2_

  - [ ]* 2.4 Write property test for anomaly injection (Property 2)
    - **Property 2: Anomaly injection produces labeled anomalies**
    - **Validates: Requirements 1.2**
    - Tag: `# Feature: aquamind-ai, Property 2`
    - File: `tests/property/test_props_simulation.py`

  - [x] 2.5 Implement DynamoDB upload script
    - Write `simulator/upload.py` with `upload_to_dynamodb(readings, pipes, table_prefix)` using boto3 batch_writer
    - Attach `ttl` (Unix epoch) and `processed=False` to each Reading; attach all Pipe metadata fields
    - Log per-record errors and continue; print summary on completion
    - _Requirements: 1.3, 9.1_

  - [ ]* 2.6 Write property test for sensor data round-trip schema integrity (Property 3)
    - **Property 3: Sensor data round-trip schema integrity**
    - **Validates: Requirements 1.3**
    - Tag: `# Feature: aquamind-ai, Property 3`
    - File: `tests/property/test_props_simulation.py`

  - [ ]* 2.7 Write property test for invalid simulation config errors (Property 4)
    - **Property 4: Invalid simulation config returns field-level errors**
    - **Validates: Requirements 1.4, 8.3**
    - Tag: `# Feature: aquamind-ai, Property 4`
    - File: `tests/property/test_props_simulation.py`

- [ ] 3. ML models
  - [x] 3.1 Implement and train Isolation Forest anomaly detector
    - Write `backend/models/train_anomaly.py`: load simulation CSV, train `IsolationForest` on `flow_rate` + `pressure`, serialize to `isolation_forest.pkl`
    - Write `backend/models/anomaly_model.py`: `load_model()`, `predict(readings) -> List[float]` returning anomaly scores ∈ [0, 1]
    - Return 503 stub if model file missing at import time
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 3.2 Implement linear regression risk predictor
    - Write `backend/models/risk_predictor.py`: `predict_failure_probability(alert_frequency_7d, anomaly_severity_avg, pipe_age_years) -> float`
    - Clamp output to [0.0, 1.0]; handle missing features by using available ones and setting `data_quality_warning`
    - _Requirements: 3.1, 3.2, 3.5_

  - [ ]* 3.3 Write property test for failure probability range (Property 7)
    - **Property 7: Failure probability is always in range**
    - **Validates: Requirements 3.1**
    - Tag: `# Feature: aquamind-ai, Property 7`
    - File: `tests/property/test_props_risk_priority.py`

  - [ ]* 3.4 Write property test for incomplete features warning (Property 9)
    - **Property 9: Incomplete features still yield prediction with warning**
    - **Validates: Requirements 3.5**
    - Tag: `# Feature: aquamind-ai, Property 9`
    - File: `tests/property/test_props_risk_priority.py`

  - [x] 3.5 Implement priority scorer
    - Write `backend/models/priority_scorer.py`: `compute_priority_score(anomaly_score, population_factor, repair_cost_factor) -> int`
    - Formula: `(anomaly_score × 0.5) + (population_factor × 0.3) + (repair_cost_factor × 0.2)`, normalized to [1, 100]
    - `assign_priority_level(failure_probability) -> str`: Critical ≥ 0.75, High 0.50–0.74, Medium 0.25–0.49, Low < 0.25
    - _Requirements: 3.3, 4.1_

  - [ ]* 3.6 Write property test for priority score range (Property 10)
    - **Property 10: Priority score is always in valid range**
    - **Validates: Requirements 4.1**
    - Tag: `# Feature: aquamind-ai, Property 10`
    - File: `tests/property/test_props_risk_priority.py`

  - [ ]* 3.7 Write property test for priority level thresholds (Property 8)
    - **Property 8: Priority level thresholds are correctly applied**
    - **Validates: Requirements 3.3**
    - Tag: `# Feature: aquamind-ai, Property 8`
    - File: `tests/property/test_props_risk_priority.py`

  - [x] 3.8 Write unit tests for ML models
    - Test known anomaly inputs produce expected scores; test precision/recall ≥ 0.80 on labeled simulation dataset
    - Test risk predictor with all features present, with missing features, and with boundary values
    - File: `tests/unit/test_anomaly_detector.py`, `tests/unit/test_risk_predictor.py`, `tests/unit/test_priority_scorer.py`
    - _Requirements: 2.3, 3.1, 3.2, 4.1_

- [x] 4. Checkpoint — Ensure all ML model tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. DynamoDB data layer
  - [x] 5.1 Implement DynamoDB client with retry logic
    - Write `backend/app/db.py`: `put_item_with_retry(table, item)` with exponential backoff (100ms, 200ms, 400ms), max 3 retries; raise after exhaustion
    - Implement `query_with_pagination(table, key_condition, limit=100, continuation_token=None) -> (items, next_token)`
    - _Requirements: 9.4_

  - [ ]* 5.2 Write property test for TTL on persisted records (Property 19)
    - **Property 19: Persisted records always include TTL**
    - **Validates: Requirements 9.1**
    - Tag: `# Feature: aquamind-ai, Property 19`
    - File: `tests/property/test_props_persistence.py`

  - [ ]* 5.3 Write property test for pagination enforcement (Property 21)
    - **Property 21: Pagination enforces maximum page size**
    - **Validates: Requirements 9.3**
    - Tag: `# Feature: aquamind-ai, Property 21`
    - File: `tests/property/test_props_persistence.py`

  - [ ]* 5.4 Write property test for historical alert sort order (Property 20)
    - **Property 20: Historical alert query returns results sorted by timestamp descending**
    - **Validates: Requirements 9.2**
    - Tag: `# Feature: aquamind-ai, Property 20`
    - File: `tests/property/test_props_persistence.py`

  - [x] 5.5 Write unit tests for DynamoDB retry logic
    - Mock 3 consecutive DynamoDB failures; verify retry count and final 500 error raised
    - Mock successful write after 2 failures; verify item written on 3rd attempt
    - File: `tests/unit/test_dynamodb_retry.py`
    - _Requirements: 9.4_

- [ ] 6. Impact Simulator module
  - [x] 6.1 Implement impact simulator
    - Write `backend/app/simulator.py`: `compute_impact(alert_id, leak_rate, population_affected, repair_cost, time_horizon_days=30) -> SimulationResult`
    - Compute ignore scenario: `total_water_loss_liters`, `financial_cost_usd`, `infrastructure_damage_score`; compute repair scenario: `repair_cost_usd`, `water_loss_prevented_liters`, `savings_usd`
    - Validate `time_horizon_days` ∈ [1, 365]; raise `ValueError` with message if out of range
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ]* 6.2 Write property test for simulation result completeness (Property 13)
    - **Property 13: Impact simulation result completeness**
    - **Validates: Requirements 5.1, 5.2**
    - Tag: `# Feature: aquamind-ai, Property 13`
    - File: `tests/property/test_props_simulation_api.py`

  - [ ]* 6.3 Write property test for time horizon boundary enforcement (Property 14)
    - **Property 14: Time horizon boundary enforcement**
    - **Validates: Requirements 5.5**
    - Tag: `# Feature: aquamind-ai, Property 14`
    - File: `tests/property/test_props_simulation_api.py`

  - [x] 6.4 Write unit tests for impact simulator
    - Test known inputs produce expected water loss and cost values
    - Test 404 on missing alert ID; test 400 on out-of-range time horizon (0, 366)
    - File: `tests/unit/test_impact_simulator.py`
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [ ] 7. Recommendation Engine
  - [x] 7.1 Implement Bedrock recommender
    - Write `backend/app/recommender.py`: `generate_recommendation(pipe_id, loss_rate, population_affected, repair_cost, time_horizon, simulation_result) -> RecommendationResponse`
    - Build structured prompt from all required fields; invoke Bedrock Claude model via boto3
    - On Bedrock error: log error, construct fallback recommendation from `simulation_result` fields; always include `recommended_action`, `savings_usd`, `repair_cost_usd`, urgency rationale
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ]* 7.2 Write property test for recommendation response completeness (Property 15)
    - **Property 15: Recommendation response always contains required fields**
    - **Validates: Requirements 6.1, 6.5**
    - Tag: `# Feature: aquamind-ai, Property 15`
    - File: `tests/property/test_props_recommendation.py`

  - [ ]* 7.3 Write property test for Bedrock prompt completeness (Property 16)
    - **Property 16: Bedrock prompt contains all required context**
    - **Validates: Requirements 6.2**
    - Tag: `# Feature: aquamind-ai, Property 16`
    - File: `tests/property/test_props_recommendation.py`

  - [x] 7.4 Write unit tests for recommender
    - Test Bedrock success path returns parsed recommendation
    - Test Bedrock error triggers fallback with all required fields present
    - File: `tests/unit/test_recommender.py`
    - _Requirements: 6.1, 6.4, 6.5_

- [ ] 8. FastAPI backend and API endpoints
  - [x] 8.1 Set up FastAPI app with Mangum adapter and structured logging
    - Write `backend/app/main.py`: create FastAPI app, register Mangum handler, add middleware that logs `timestamp`, `request_id`, `endpoint`, `response_status_code` to CloudWatch
    - Write `backend/app/responses.py`: `success_response(data)` and `error_response(message)` helpers enforcing the standard envelope
    - _Requirements: 8.2, 8.6_

  - [ ]* 8.2 Write property test for API response envelope (Property 17)
    - **Property 17: API response envelope is always present**
    - **Validates: Requirements 8.2**
    - Tag: `# Feature: aquamind-ai, Property 17`
    - File: `tests/property/test_props_api.py`

  - [ ]* 8.3 Write property test for structured log output (Property 18)
    - **Property 18: Structured log output contains required fields**
    - **Validates: Requirements 8.6**
    - Tag: `# Feature: aquamind-ai, Property 18`
    - File: `tests/property/test_props_api.py`

  - [x] 8.4 Implement `POST /simulate` endpoint
    - Validate request body with Pydantic; call simulator upload logic; return 422 on missing fields
    - _Requirements: 1.4, 8.3_

  - [x] 8.5 Implement `GET /pipes` endpoint
    - Query Pipes table; return paginated list with all pipe metadata fields
    - _Requirements: 8.1, 9.3_

  - [x] 8.6 Implement `GET /alerts` endpoint
    - Query Alerts table sorted by `priority_score` descending; support pagination (max 100/page, continuation token); include `immediate_action_required` flag for Critical alerts
    - _Requirements: 4.2, 4.3, 9.2, 9.3_

  - [ ]* 8.7 Write property test for alerts sort order (Property 11)
    - **Property 11: Alerts API returns results sorted by priority descending**
    - **Validates: Requirements 4.2**
    - Tag: `# Feature: aquamind-ai, Property 11`
    - File: `tests/property/test_props_risk_priority.py`

  - [ ]* 8.8 Write property test for critical alert flag (Property 12)
    - **Property 12: Critical alerts carry the immediate action flag**
    - **Validates: Requirements 4.3**
    - Tag: `# Feature: aquamind-ai, Property 12`
    - File: `tests/property/test_props_risk_priority.py`

  - [x] 8.9 Implement `POST /detect` endpoint
    - Accept batch of sensor readings; run anomaly model; run risk predictor and priority scorer; persist Alerts to DynamoDB with TTL; return 503 if model file missing
    - _Requirements: 2.1, 2.2, 2.4, 3.1, 3.3, 4.1, 9.1_

  - [x] 8.10 Implement `POST /whatif` endpoint
    - Validate `alert_id` exists (404 if not); validate `time_horizon_days` ∈ [1, 365] (400 if not); call `compute_impact`; persist SimulationResult with TTL; return result
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1_

  - [x] 8.11 Implement `POST /explain` endpoint
    - Validate request; call `generate_recommendation`; persist result; return recommendation envelope
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 8.12 Write unit tests for all API endpoints
    - Test each endpoint: success path, 422 on invalid payload, 404 on missing alert, 400 on bad time horizon, 503 on missing model, 500 after DynamoDB retry exhaustion
    - Test unhandled exception returns 500 with `request_id`
    - File: `tests/unit/test_api_endpoints.py`
    - _Requirements: 8.2, 8.3, 8.5_

- [x] 9. Checkpoint — Ensure all backend and API tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Anomaly Detector Lambda
  - [x] 10.1 Implement scheduled detector handler
    - Write `backend/detector/handler.py`: `handler(event, context)` — query `processed-timestamp-index` GSI for unprocessed Readings, run Isolation Forest, create Alert records for scores above threshold, mark Readings as processed, write Alerts to DynamoDB
    - _Requirements: 2.1, 2.2, 9.1_

  - [ ]* 10.2 Write property test for every reading receives a classification (Property 5)
    - **Property 5: Every reading receives a classification**
    - **Validates: Requirements 2.1**
    - Tag: `# Feature: aquamind-ai, Property 5`
    - File: `tests/property/test_props_detection.py`

  - [ ]* 10.3 Write property test for anomalous readings produce complete Alert records (Property 6)
    - **Property 6: Anomalous readings produce complete Alert records**
    - **Validates: Requirements 2.2**
    - Tag: `# Feature: aquamind-ai, Property 6`
    - File: `tests/property/test_props_detection.py`

  - [x] 10.4 Write unit tests for anomaly detector handler
    - Test batch of 1,000 readings processed within 5 seconds
    - Test detector writes correct Alert fields; test 503 on missing model file
    - File: `tests/unit/test_anomaly_detector.py`
    - _Requirements: 2.2, 2.4, 2.5_

- [x] 11. React Dashboard
  - [x] 11.1 Set up React app with TypeScript, API client, and polling
    - Scaffold `frontend/src/` with `api.ts` (axios client, `REACT_APP_API_URL` base URL), `useAlerts` hook polling `GET /alerts` every 30 seconds, global error state
    - _Requirements: 7.1, 7.5_

  - [x] 11.2 Implement AlertsPanel component
    - Write `frontend/src/components/AlertsPanel.tsx`: render sorted alert list with priority badges (Critical/High/Medium/Low color coding), `immediate_action_required` indicator, click handler to select alert
    - _Requirements: 7.1, 7.2_

  - [ ]* 11.3 Write property test for dashboard state preservation on API error (Property 22)
    - **Property 22: Dashboard preserves state on API error**
    - **Validates: Requirements 7.5**
    - Tag: `// Feature: aquamind-ai, Property 22`
    - File: `tests/frontend/AlertsPanel.test.tsx`
    - Use `fast-check` with min 100 runs

  - [x] 11.4 Implement SensorGraph component
    - Write `frontend/src/components/SensorGraph.tsx`: render flow rate and pressure trend charts for selected pipe using a charting library (e.g. recharts); fetch node sensor history on alert select
    - _Requirements: 7.2_

  - [x] 11.5 Implement MapView component
    - Write `frontend/src/components/MapView.tsx`: render color-coded pipe network (risk level → color); click pipe to select and show detail
    - _Requirements: 7.1, 7.2_

  - [x] 11.6 Implement ImpactSimulator panel
    - Write `frontend/src/components/ImpactSimulator.tsx`: "Analyze Impact" button calls `POST /whatif`; display ignore vs. repair scenarios side by side; show error in panel on failure without losing alert detail
    - _Requirements: 7.3, 7.5_

  - [x] 11.7 Implement RecommendationPanel component
    - Write `frontend/src/components/RecommendationPanel.tsx`: call `POST /explain` after simulation; render AI recommendation text; show "Recommendation unavailable" on error
    - _Requirements: 7.4, 7.5_

  - [x] 11.8 Wire all components into App
    - Write `frontend/src/App.tsx`: compose MapView, AlertsPanel, SensorGraph, ImpactSimulator, RecommendationPanel; wire shared alert selection state; display global error banner on API failure without unmounting existing data
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 11.9 Write unit tests for frontend components
    - Test AlertsPanel renders sorted alerts and priority badges; test error banner shown on API failure; test existing alert list preserved on error
    - File: `tests/frontend/AlertsPanel.test.tsx`
    - _Requirements: 7.1, 7.5_

- [x] 12. Checkpoint — Ensure all frontend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. AWS SAM infrastructure
  - [x] 13.1 Write SAM template for Lambda functions and API Gateway
    - Write `infra/template.yaml`: define `ApiHandlerFunction` (Python 3.11, 512MB, 29s timeout, API Gateway trigger for all routes) and `AnomalyDetectorFunction` (Python 3.11, 256MB, 300s timeout, EventBridge schedule every 5 minutes)
    - Add IAM policies for DynamoDB access and Bedrock invocation
    - _Requirements: 8.4, 8.5_

  - [x] 13.2 Define DynamoDB tables and GSIs in SAM template
    - Add `PipesTable`, `ReadingsTable` (with `processed-timestamp-index` GSI), `AlertsTable` (with `pipe-timestamp-index` GSI), `SimulationResultsTable` — all on-demand billing
    - Configure TTL attribute on Readings, Alerts, SimulationResults tables
    - _Requirements: 9.1, 9.2_

  - [x] 13.3 Define S3 bucket and CloudFront distribution for frontend
    - Add S3 bucket (static website hosting) and CloudFront distribution with OAI in `infra/template.yaml`
    - Add `frontend/deploy.sh` script: `npm run build`, sync to S3, invalidate CloudFront cache
    - _Requirements: 7.6_

  - [x] 13.4 Write SAM build and deploy configuration
    - Write `infra/samconfig.toml` with default stack name, region, and S3 deployment bucket
    - Write `Makefile` targets: `make build` (SAM build + React build), `make deploy` (SAM deploy), `make simulate` (run simulator upload script)
    - _Requirements: 8.4_

- [x] 14. End-to-end demo flow integration test
  - [x] 14.1 Write integration test for full demo flow
    - Write `tests/unit/test_e2e_demo.py`: mock DynamoDB and Bedrock; run simulate → detect → score → whatif → explain in sequence; assert Alert created, priority score assigned, SimulationResult returned, recommendation contains required fields
    - Assert full flow completes within 60 seconds
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 15. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use `hypothesis` (Python backend) and `fast-check` (TypeScript frontend), minimum 100 iterations each
- Every property test must include the comment tag `# Feature: aquamind-ai, Property N: <property_text>`
- Unit tests cover specific examples, integration points, and all error conditions — not duplicating what property tests already cover
- Checkpoints ensure incremental validation before moving to the next subsystem
