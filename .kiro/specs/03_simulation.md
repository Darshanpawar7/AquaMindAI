# Simulation System

## Goal
Generate realistic synthetic water network data.

## Approach
- Use Python (NumPy, Faker)
- Simulate EPANET-like network

## Network
- 200 pipes
- 100 junctions

## Data
- Flow (m³/h)
- Pressure (psi)
- Time-series (hourly for 90 days)

## Anomalies
- Leak → pressure drop + flow increase
- Gradual degradation
- Random noise

## Additional Data
- Population affected per pipe
- Repair cost estimation

## Output
- CSV files
- DynamoDB upload script

## Requirements
- At least 10 anomalies
- Clean structured dataset

## Test
- Verify anomalies exist
- Validate data ranges