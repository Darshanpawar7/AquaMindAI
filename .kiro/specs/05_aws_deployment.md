# AWS Deployment

## Architecture

- S3 → frontend hosting
- API Gateway → API layer
- Lambda → backend logic
- DynamoDB → data storage
- Bedrock → AI recommendations
- CloudWatch → scheduled detection

## Purpose of Each Service

- Lambda → real-time processing
- DynamoDB → fast data retrieval
- Bedrock → intelligent insights
- S3 → scalable hosting
- API Gateway → secure endpoints

## Infrastructure
Use AWS SAM template.yaml

## Resources
- Tables: Pipes, Alerts, Readings
- Lambda functions:
  - API handler
  - Anomaly detector (scheduled)

## Deployment Steps
1. sam build
2. sam deploy --guided
3. Upload frontend to S3

## Post-Deployment Tests
- API working
- Dashboard loads
- Alerts visible
- Impact Simulator works

## Scalability
Serverless architecture ensures automatic scaling across cities.