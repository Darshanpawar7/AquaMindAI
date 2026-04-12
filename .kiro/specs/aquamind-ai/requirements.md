# Requirements Document

## Introduction

AquaMind AI is an AI-powered digital twin platform for smart water systems. It simulates urban water networks, detects anomalies in real-time sensor data, predicts infrastructure failures, and recommends cost-optimized repair actions using an Impact Simulator. The platform targets municipal engineers and infrastructure planners who need decision intelligence to reduce water loss, prioritize maintenance, and justify repair investments.

## Glossary

- **AquaMind_AI**: The overall platform encompassing all subsystems described in this document
- **Digital_Twin**: A virtual simulation model of a physical water network, updated with real or simulated sensor data
- **Anomaly_Detector**: The ML subsystem responsible for identifying abnormal patterns in flow and pressure sensor readings
- **Risk_Predictor**: The ML subsystem that estimates the probability and severity of infrastructure failures
- **Priority_Scorer**: The subsystem that assigns a numeric priority score to detected anomalies based on risk, impact, and urgency
- **Impact_Simulator**: The subsystem that models the projected cost and damage of ignoring vs. repairing a detected issue
- **Recommendation_Engine**: The Generative AI subsystem (backed by Amazon Bedrock) that produces natural-language repair recommendations with cost-benefit analysis
- **Dashboard**: The React-based frontend that displays alerts, scores, simulation results, and AI recommendations
- **Sensor_Data**: Time-series readings of flow rate and pressure from simulated or real network nodes
- **Alert**: A record created when the Anomaly_Detector identifies an anomalous condition, including node ID, timestamp, anomaly type, and priority score
- **Simulation_Result**: The output of the Impact_Simulator containing projected water loss, financial cost, and infrastructure damage for a given scenario
- **API**: The FastAPI backend deployed as AWS Lambda functions, exposed via API Gateway

---

## Requirements

### Requirement 1: Sensor Data Simulation

**User Story:** As a municipal engineer, I want the platform to simulate realistic water network sensor data, so that I can evaluate the system's detection capabilities without requiring live infrastructure.

#### Acceptance Criteria

1. THE Digital_Twin SHALL generate time-series Sensor_Data for at least 10 network nodes, each producing flow rate and pressure readings at configurable intervals.
2. WHEN a simulation run is initiated, THE Digital_Twin SHALL inject synthetic anomalies (leak events, pressure drops) into the generated Sensor_Data at a configurable rate.
3. THE Digital_Twin SHALL store generated Sensor_Data in DynamoDB with a schema that includes node ID, timestamp, flow rate, pressure, and anomaly label.
4. IF the simulation configuration is missing required parameters, THEN THE Digital_Twin SHALL return a descriptive validation error identifying the missing fields.

---

### Requirement 2: Anomaly Detection

**User Story:** As a municipal engineer, I want the system to automatically detect anomalies in sensor data, so that I can identify leaks and pressure irregularities without manual inspection.

#### Acceptance Criteria

1. WHEN new Sensor_Data is available, THE Anomaly_Detector SHALL evaluate each reading against a trained ML model and classify it as normal or anomalous.
2. WHEN an anomalous reading is detected, THE Anomaly_Detector SHALL create an Alert record containing node ID, timestamp, anomaly type, and raw sensor values.
3. THE Anomaly_Detector SHALL achieve a minimum precision of 0.80 and recall of 0.80 on the labeled simulation dataset.
4. IF the ML model file is unavailable at startup, THEN THE Anomaly_Detector SHALL log the error and return a 503 response to any detection request.
5. THE Anomaly_Detector SHALL process a batch of 1,000 Sensor_Data records within 5 seconds.

---

### Requirement 3: Failure Risk Prediction

**User Story:** As an infrastructure planner, I want the system to predict the probability of infrastructure failure for each network node, so that I can plan proactive maintenance before failures occur.

#### Acceptance Criteria

1. WHEN an Alert is created, THE Risk_Predictor SHALL compute a failure probability score between 0.0 and 1.0 for the affected node.
2. THE Risk_Predictor SHALL incorporate historical Alert frequency, anomaly severity, and node age as input features.
3. WHEN the Risk_Predictor produces a failure probability score, THE Priority_Scorer SHALL assign a priority level of Critical (≥0.75), High (0.50–0.74), Medium (0.25–0.49), or Low (<0.25).
4. THE Risk_Predictor SHALL return a prediction result within 2 seconds per node.
5. IF input features for a node are incomplete, THEN THE Risk_Predictor SHALL return a prediction using available features and include a data quality warning in the response.

---

### Requirement 4: Priority Scoring and Alert Management

**User Story:** As a municipal engineer, I want detected anomalies ranked by priority, so that I can focus repair resources on the most critical issues first.

#### Acceptance Criteria

1. THE Priority_Scorer SHALL assign a numeric priority score from 1 (lowest) to 100 (highest) to each Alert, derived from failure probability, estimated water loss rate, and node criticality.
2. WHEN multiple Alerts exist, THE API SHALL return them ordered by priority score in descending order.
3. WHEN an Alert's priority level is Critical, THE API SHALL include a flag in the Alert response payload indicating immediate action is required.
4. THE Priority_Scorer SHALL recalculate the priority score for an Alert when new Sensor_Data is received for the same node.

---

### Requirement 5: Impact Simulation (What-If Analysis)

**User Story:** As an infrastructure planner, I want to simulate the projected impact of ignoring vs. repairing a detected issue, so that I can justify repair decisions with quantified cost-benefit data.

#### Acceptance Criteria

1. WHEN an engineer requests an impact simulation for an Alert, THE Impact_Simulator SHALL compute a Simulation_Result for both the "ignore" and "repair" scenarios.
2. THE Impact_Simulator SHALL include in each Simulation_Result: projected water loss in liters, estimated financial cost in USD, and projected infrastructure damage score over a configurable time horizon (default 30 days).
3. THE Impact_Simulator SHALL return a Simulation_Result within 3 seconds of receiving a valid simulation request.
4. IF a simulation request references an Alert ID that does not exist, THEN THE Impact_Simulator SHALL return a 404 error with a descriptive message.
5. THE Impact_Simulator SHALL accept a time horizon parameter between 1 and 365 days; IF a value outside this range is provided, THEN THE Impact_Simulator SHALL return a 400 error.

---

### Requirement 6: AI-Generated Repair Recommendations

**User Story:** As a municipal engineer, I want AI-generated repair recommendations with cost-benefit analysis, so that I can make informed, data-backed maintenance decisions quickly.

#### Acceptance Criteria

1. WHEN a Simulation_Result is available for an Alert, THE Recommendation_Engine SHALL generate a natural-language repair recommendation that includes the recommended action, estimated cost savings, and urgency rationale.
2. THE Recommendation_Engine SHALL invoke Amazon Bedrock with a structured prompt containing the Alert details, Risk_Predictor output, and Simulation_Result data.
3. THE Recommendation_Engine SHALL return a recommendation within 10 seconds of receiving a valid request.
4. IF the Amazon Bedrock service returns an error, THEN THE Recommendation_Engine SHALL return a fallback recommendation derived from the Simulation_Result data without natural language generation.
5. THE Recommendation_Engine SHALL include the repair cost estimate and projected savings in every recommendation response, regardless of whether natural language generation succeeded.

---

### Requirement 7: Interactive Dashboard

**User Story:** As a municipal engineer, I want an interactive web dashboard, so that I can monitor alerts, view priority scores, run simulations, and read AI recommendations in one place.

#### Acceptance Criteria

1. THE Dashboard SHALL display a list of all active Alerts sorted by priority score in descending order, refreshed at a configurable interval (default 30 seconds).
2. WHEN an engineer selects an Alert, THE Dashboard SHALL display the associated priority score, failure probability, and node sensor history.
3. WHEN an engineer triggers an impact simulation from the Dashboard, THE Dashboard SHALL display the Simulation_Result for both "ignore" and "repair" scenarios side by side.
4. WHEN a Recommendation_Engine response is available, THE Dashboard SHALL render the natural-language recommendation in a dedicated panel.
5. THE Dashboard SHALL remain functional and display a user-visible error message WHEN any API call fails, without crashing or losing existing displayed data.
6. THE Dashboard SHALL be accessible via a public URL served from AWS S3 with CloudFront or equivalent static hosting.

---

### Requirement 8: API and Backend Infrastructure

**User Story:** As a developer, I want a well-structured REST API deployed on AWS, so that the frontend and any future integrations can reliably access all platform capabilities.

#### Acceptance Criteria

1. THE API SHALL expose endpoints for: submitting Sensor_Data, retrieving Alerts, triggering anomaly detection, requesting impact simulation, and fetching recommendations.
2. THE API SHALL return responses conforming to a consistent JSON schema, including a `status` field (`success` or `error`) and a `data` or `error_message` field in every response.
3. WHEN a request payload fails schema validation, THE API SHALL return a 422 response with a field-level error description.
4. THE API SHALL be deployed as AWS Lambda functions behind API Gateway and SHALL handle at least 50 concurrent requests without returning 5xx errors under normal operating conditions.
5. IF a Lambda function execution exceeds 29 seconds, THEN THE API SHALL return a 504 timeout response to the caller.
6. THE API SHALL log all requests and errors to AWS CloudWatch with a structured log format including timestamp, request ID, endpoint, and response status code.

---

### Requirement 9: Data Persistence and Retrieval

**User Story:** As a municipal engineer, I want all sensor readings, alerts, and simulation results persisted, so that I can review historical data and audit past decisions.

#### Acceptance Criteria

1. THE API SHALL persist all Sensor_Data, Alerts, and Simulation_Results to DynamoDB with a time-to-live (TTL) attribute configurable per record type.
2. WHEN an engineer queries historical Alerts for a node, THE API SHALL return all Alerts for that node ordered by timestamp in descending order.
3. THE API SHALL support pagination for Alert and Sensor_Data queries, returning a maximum of 100 records per page with a continuation token.
4. IF a DynamoDB write operation fails, THEN THE API SHALL retry the operation up to 3 times with exponential backoff before returning a 500 error.

---

### Requirement 10: End-to-End Demo Flow

**User Story:** As a stakeholder, I want a complete end-to-end demo that exercises all platform capabilities, so that I can validate the system meets its success criteria.

#### Acceptance Criteria

1. THE AquaMind_AI platform SHALL support a demo flow that: generates Sensor_Data, detects at least one anomaly, assigns a priority score, runs an Impact_Simulator scenario, and displays an AI-generated recommendation — all within a single user session.
2. WHEN the demo flow completes successfully, THE Dashboard SHALL display a summary view showing the detected Alert, its priority score, the Simulation_Result comparison, and the Recommendation_Engine output.
3. THE AquaMind_AI platform SHALL complete the full end-to-end demo flow within 60 seconds of initiation.
