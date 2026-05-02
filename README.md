# AquaMind AI

**Intelligent Water Infrastructure Monitoring & Predictive Maintenance Platform**

*By [Darshan P Pawar](https://github.com/DarshanPawar)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-FF9900.svg)](https://aws.amazon.com/lambda/)

## 🌊 Overview

AquaMind AI is a serverless, AI-powered water infrastructure management platform designed to detect anomalies in water distribution networks, predict pipe failures, and provide actionable recommendations for maintenance prioritization. By combining machine learning anomaly detection, statistical risk modeling, and generative AI insights, AquaMind enables water utilities to transition from reactive maintenance to predictive, data-driven operations.

### Key Capabilities

- **Real-time Anomaly Detection**: Isolate unusual sensor readings (flow rate, pressure) across pipeline networks using machine learning
- **Predictive Risk Assessment**: Forecast pipe failure probability based on historical alerts, anomaly patterns, and infrastructure age
- **Impact Simulation**: Model "what-if" scenarios (repair vs. ignore) with quantified financial and environmental impact
- **AI-Powered Recommendations**: Generate intelligent repair prioritization suggestions using Claude 3 (via Amazon Bedrock)
- **Multi-view Dashboard**: Comprehensive monitoring with command center, network visualization, alerts, and analytics
- **Serverless Architecture**: Scalable, cost-efficient AWS Lambda + DynamoDB backend; zero infrastructure management

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## 🏗️ Architecture Overview

AquaMind AI follows a modern serverless, full-stack architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)                │
│         (Hosted on S3 + CloudFront via AWS CDN)                │
│                                                                 │
│  Dashboard | Alerts | Analytics | Pipe Network | Simulations  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST API
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              AWS API Gateway + Lambda (FastAPI)                │
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │  Alerts    │  │  Detect    │  │  What-If   │  ...          │
│  │  Endpoint  │  │  Endpoint  │  │  Endpoint  │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐  ┌─────────┐  ┌──────────┐
        │DynamoDB  │  │Bedrock  │  │Local ML  │
        │(Pipes,   │  │(Claude) │  │Models    │
        │Readings, │  │(AI Recs)│  │(Anomaly, │
        │Alerts)   │  │         │  │Risk)     │
        └──────────┘  └─────────┘  └──────────┘
```

### Component Breakdown

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Presentation** | React 18, TypeScript, Tailwind CSS, Recharts | Interactive UI for monitoring and analysis |
| **API** | FastAPI, Mangum | High-performance REST API with ASGI/Lambda support |
| **Compute** | AWS Lambda (Python 3.11) | Serverless function execution |
| **Data** | AWS DynamoDB | NoSQL time-series data store |
| **ML Models** | scikit-learn, IsolationForest | Anomaly detection & risk prediction |
| **AI** | Amazon Bedrock, Claude 3 Haiku | Generative AI for recommendations |
| **IaC** | AWS SAM, CloudFormation | Infrastructure as code |

---

## ✨ Features

### 🔍 Anomaly Detection
- **IsolationForest Algorithm**: Detect outliers in sensor readings (flow, pressure) without labeled training data
- **Real-time Scoring**: Anomaly scores in [0, 1] scale (1 = most anomalous)
- **Batch Detection**: Process multiple readings in a single request

### 📊 Risk Prediction
- **Multi-factor Model**: Combines alert frequency, anomaly severity, and pipe age
- **Failure Probability**: Quantified risk assessment for prioritization
- **Data Quality Awareness**: Graceful handling of incomplete feature sets

### 🎯 Priority Scoring
- **Dynamic Prioritization**: Integrate anomaly severity, risk, and infrastructure criticality
- **Four Tiers**: Critical, High, Medium, Low alert levels
- **Action Triggers**: Flag immediate-action-required alerts for operator dashboard

### 💡 What-If Impact Simulation
- **Dual Scenario Modeling**: Compare financial/environmental impact of repair vs. ignore strategies
- **Water Loss Quantification**: Compute cumulative water loss over time horizons
- **Cost-Benefit Analysis**: ROI calculations for maintenance decisions

### 🤖 AI-Powered Recommendations
- **Claude 3 Integration**: Natural language recommendations via Amazon Bedrock
- **Context-Aware**: Incorporates pipe characteristics, population impact, and simulation data
- **Fallback Logic**: Deterministic recommendations when AI service unavailable

### 📱 Interactive Dashboard
- **Command Center**: Summary view of critical alerts and system health
- **Pipe Network Map**: Visual representation of infrastructure with anomaly indicators
- **Live Alerts Panel**: Sortable, real-time alert monitoring with drill-down
- **Analytics View**: Historical trends, failure distribution, maintenance ROI
- **Simulation View**: Interactive what-if scenario builder with impact visualization
- **Dark/Light Themes**: Accessibility and user preference

### ⚡ Resilience & Offline Support
- **Local Fallback Store**: Continue operations during DynamoDB outages
- **Graceful Degradation**: Model unavailability returns 503; system remains operational
- **Pagination Support**: Efficient handling of large alert/pipe datasets

---

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.110+
- **ASGI Server**: Uvicorn
- **AWS Integration**: Boto3, Mangum (Lambda adapter)
- **ML/Data Science**: scikit-learn, NumPy, joblib
- **Validation**: Pydantic 2.6+
- **Testing**: pytest, pytest-asyncio, hypothesis

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript 5.4+
- **Build Tool**: Vite 5.2+
- **Styling**: Tailwind CSS 3.4+, PostCSS
- **UI Components**: Lucide React (icons), Framer Motion (animations)
- **Charts**: Recharts 2.12+
- **HTTP Client**: Axios 1.6+
- **Testing**: Jest 29+, React Testing Library

### Infrastructure
- **Serverless**: AWS Lambda, API Gateway
- **Database**: AWS DynamoDB
- **AI/ML**: Amazon Bedrock (Claude 3 Haiku)
- **Storage**: AWS S3, CloudFront CDN
- **IaC**: AWS SAM, CloudFormation

### DevOps
- **Deployment**: GNU Make, Bash
- **Version Control**: Git
- **Package Management**: pip (Python), npm (Node.js)

---

## 📦 Installation & Setup

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **AWS Account** with credentials configured (for cloud deployment)
- **AWS CLI** v2+
- **AWS SAM CLI** for local Lambda testing
- **Git** for version control

### Local Development Setup

#### 1. Clone Repository

```bash
git clone https://github.com/DarshanPawar/AquaMindAI.git
cd AquaMindAI
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

#### 3. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

#### 4. Configure AWS Credentials

```bash
aws configure
# Enter AWS Access Key ID, Secret Access Key, region (us-east-1), output format (json)
```

#### 5. Set Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
export TABLE_PREFIX=aquamind
export AWS_DEFAULT_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
export DRY_RUN=false
```

---

## 🚀 Usage

### Local Development

#### Start Backend API (Local)

```bash
# Run FastAPI dev server (auto-reload on changes)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs` (Swagger UI)

#### Start Frontend (Local)

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

#### Run Data Simulator

Generate synthetic sensor data and upload to DynamoDB:

```bash
# Dry-run (preview data without writing)
make simulate-dry

# Full simulation (writes to DynamoDB)
make simulate
```

**Parameters** (in Makefile):
- `num_pipes`: Number of water pipes to simulate (default: 200)
- `days`: Duration of simulation in days (default: 90)
- `anomaly_rate`: Percentage of readings with anomalies (default: 5%)

### Docker Development (Optional)

```bash
# Build Docker image for backend
docker build -t aquamind-api:latest backend/

# Run container locally
docker run -p 8000:8000 -e TABLE_PREFIX=aquamind aquamind-api:latest
```

---

## 📡 API Endpoints

### Base URL
- **Local**: `http://localhost:8000`
- **AWS**: `https://<api-id>.execute-api.<region>.amazonaws.com/prod`

### Core Endpoints

#### 1. **Health Check**
```
GET /health
```
Returns: `{"status": "ok"}`

#### 2. **Get Pipes**
```
GET /pipes?continuation_token=<optional_token>
```
**Response** (200):
```json
{
  "status": "success",
  "data": {
    "pipes": [
      {
        "pipe_id": "pipe_001",
        "junction_start": "junc_001",
        "junction_end": "junc_002",
        "length_m": 500.0,
        "diameter_mm": 100,
        "age_years": 25,
        "population_affected": 5000,
        "repair_cost_usd": 50000,
        "material": "asbestos_cement"
      }
    ],
    "continuation_token": null
  }
}
```

#### 3. **Run Anomaly Detection**
```
POST /detect
Content-Type: application/json
```
**Request Body**:
```json
{
  "readings": [
    {
      "pipe_id": "pipe_001",
      "timestamp": "2026-05-02T10:30:00Z",
      "flow_rate": 45.2,
      "pressure": 3.2,
      "anomaly_label": null
    }
  ]
}
```
**Response** (200):
```json
{
  "status": "success",
  "data": {
    "alerts_created": 1,
    "detection_summary": {
      "total_readings": 1,
      "anomalies_detected": 1,
      "processing_time_ms": 42
    }
  }
}
```

#### 4. **Get Alerts**
```
GET /alerts?continuation_token=<optional_token>
```
**Response** (200):
```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "alert_id": "alert_abc123",
        "pipe_id": "pipe_001",
        "timestamp": "2026-05-02T10:30:00Z",
        "anomaly_type": "pressure_spike",
        "anomaly_score": 0.87,
        "failure_probability": 0.65,
        "priority_score": 8,
        "priority_level": "Critical",
        "immediate_action_required": true,
        "flow_rate": 45.2,
        "pressure": 3.2
      }
    ],
    "continuation_token": null
  }
}
```

#### 5. **Impact Simulation (What-If)**
```
POST /whatif
Content-Type: application/json
```
**Request Body**:
```json
{
  "alert_id": "alert_abc123",
  "leak_rate": 2.5,
  "population_affected": 5000,
  "repair_cost": 50000,
  "time_horizon_days": 30
}
```
**Response** (200):
```json
{
  "status": "success",
  "data": {
    "simulation_id": "sim_xyz789",
    "alert_id": "alert_abc123",
    "ignore_scenario": {
      "total_water_loss_liters": 180000,
      "financial_cost_usd": 18000,
      "population_impact": "High"
    },
    "repair_scenario": {
      "repair_cost_usd": 50000,
      "water_saved_liters": 180000
    },
    "savings_usd": 32000,
    "recommendation": "Prioritize repair — negative financial impact..."
  }
}
```

#### 6. **Get AI Recommendation**
```
POST /explain
Content-Type: application/json
```
**Request Body**:
```json
{
  "alert_id": "alert_abc123",
  "simulation_id": "sim_xyz789"
}
```
**Response** (200):
```json
{
  "status": "success",
  "data": {
    "recommendation": "Critical: Immediate repair recommended...",
    "reasoning": "...",
    "source": "claude_3_haiku"
  }
}
```

### Error Responses

**400 Bad Request**:
```json
{"status": "error", "error_message": "Invalid input..."}
```

**503 Service Unavailable** (Model not available):
```json
{"status": "error", "error_message": "Model not available: ..."}
```

**Full API Documentation**: Interactive Swagger UI available at `/docs` endpoint

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TABLE_PREFIX` | `aquamind` | DynamoDB table name prefix |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region for DynamoDB and Bedrock |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-haiku-20240307-v1:0` | Claude model ID for recommendations |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DRY_RUN` | `false` | Simulator: set to `true` for preview without DynamoDB writes |

### DynamoDB Tables

The system automatically creates these tables (via SAM template):

| Table | Partition Key | Sort Key | Purpose |
|-------|---------------|----------|---------|
| `{PREFIX}-Pipes` | `pipe_id` | — | Water pipe metadata |
| `{PREFIX}-Readings` | `pipe_id` | `timestamp` | Time-series sensor data |
| `{PREFIX}-Alerts` | `alert_id` | — | Anomaly alerts with priority |
| `{PREFIX}-SimulationResults` | `simulation_id` | — | What-if scenario results |

### Frontend Configuration

Edit [frontend/vite.config.ts](frontend/vite.config.ts) for:
- API base URL
- Build optimization
- Dev server port

---

## 🧪 Testing

### Backend Tests

Run all backend tests:

```bash
pytest -v --tb=short
```

Test categories:

```bash
# Unit tests
pytest tests/unit/ -v

# Anomaly detection model
pytest tests/unit/test_anomaly_model.py -v

# API endpoints
pytest tests/unit/test_api_endpoints.py -v

# Risk prediction
pytest tests/unit/test_risk_predictor.py -v

# Recommendation engine
pytest tests/unit/test_recommender.py -v

# Impact simulator
pytest tests/unit/test_impact_simulator.py -v

# End-to-end integration
pytest tests/unit/test_e2e_demo.py -v
```

### Frontend Tests

Run all frontend tests:

```bash
cd frontend
npm test

# Watch mode
npm run test:watch
```

Test coverage:

```bash
npm test -- --coverage
```

### Property-Based Testing

```bash
# Tests with hypothesis (property-based testing)
pytest tests/property/ -v
```

### Test Coverage Report

```bash
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

---

## 🚢 Deployment

### AWS Deployment (Production)

#### Prerequisites
- AWS account with appropriate permissions (Lambda, DynamoDB, Bedrock, CloudFront)
- AWS CLI configured
- AWS SAM CLI installed

#### 1. Build

```bash
make build
```

Builds both backend (SAM) and frontend (npm).

#### 2. Deploy Backend

```bash
# First deployment (interactive)
make deploy

# Subsequent deployments
make deploy STACK_NAME=aquamind-ai ENV=prod REGION=us-east-1
```

Outputs:
- Lambda function ARN
- API Gateway endpoint URL
- DynamoDB table names

#### 3. Deploy Frontend

After backend deployment, get the API URL and S3 bucket from CloudFormation outputs:

```bash
make deploy-frontend \
  S3_BUCKET=aquamind-ui-prod \
  CF_DIST_ID=E1234ABCD \
  API_URL=https://api.aquamind.example.com
```

#### 4. Verify Deployment

```bash
# Test health endpoint
curl https://api.aquamind.example.com/health

# Open frontend in browser
https://aquamind.example.com
```

### Environment-Specific Deployment

```bash
# Staging
make deploy ENV=staging STACK_NAME=aquamind-staging

# Development
make deploy ENV=dev STACK_NAME=aquamind-dev

# Production
make deploy ENV=prod STACK_NAME=aquamind-ai
```

### Monitoring & Logs

```bash
# Tail Lambda logs
aws logs tail /aws/lambda/aquamind-api-handler-prod --follow

# View DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=aquamind-Alerts
```

---

## 📁 Project Structure

```
AquaMindAI/
├── backend/                          # Python FastAPI backend
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── db.py                     # DynamoDB utilities
│   │   ├── local_store.py            # Fallback in-memory store
│   │   ├── models.py                 # Pydantic data models
│   │   ├── schemas.py                # Request/response schemas
│   │   ├── responses.py              # Response formatters
│   │   ├── simulator.py              # Impact simulation logic
│   │   ├── recommender.py            # AI recommendation engine
│   │   ├── routers/                  # API endpoint modules
│   │   │   ├── alerts.py             # GET /alerts
│   │   │   ├── detect.py             # POST /detect
│   │   │   ├── explain.py            # POST /explain (AI recs)
│   │   │   ├── pipes.py              # GET /pipes
│   │   │   ├── seed.py               # POST /seed (data loading)
│   │   │   ├── simulate.py           # POST /simulate
│   │   │   └── whatif.py             # POST /whatif
│   │   └── detector/                 # Anomaly detection
│   │       ├── __init__.py
│   │       └── handler.py
│   └── models/                       # ML models
│       ├── __init__.py
│       ├── anomaly_model.py          # IsolationForest interface
│       ├── isolation_forest.pkl      # Trained model (binary)
│       ├── priority_scorer.py        # Priority level assignment
│       ├── risk_predictor.py         # Failure probability model
│       └── train_anomaly.py          # Model training script
│
├── frontend/                         # React + TypeScript frontend
│   ├── public/
│   ├── src/
│   │   ├── api.ts                    # API client (axios)
│   │   ├── App.tsx                   # Root component
│   │   ├── index.tsx                 # React entry point
│   │   ├── index.css                 # Global styles
│   │   ├── components/
│   │   │   ├── DashboardView.tsx     # Command center
│   │   │   ├── PipeNetworkView.tsx   # Network visualization
│   │   │   ├── AlertsView.tsx        # Alert list + details
│   │   │   ├── AnalyticsView.tsx     # Trend analysis
│   │   │   ├── SimulateView.tsx      # What-if simulator
│   │   │   ├── AIInsightsPanel.tsx   # Recommendation display
│   │   │   ├── AlertsPanel.tsx       # Alert summary
│   │   │   ├── RecommendationPanel.tsx
│   │   │   ├── ImpactSimulator.tsx
│   │   │   ├── MapView.tsx           # GIS visualization
│   │   │   └── SensorGraph.tsx       # Time-series charts
│   │   └── hooks/
│   │       └── useAlerts.ts          # Custom hook for alerts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── jest.config.js
│
├── infra/                            # AWS infrastructure (IaC)
│   ├── template.yaml                 # SAM CloudFormation template
│   └── samconfig.toml                # SAM deployment config
│
├── simulator/                        # Data generation & uploads
│   ├── __init__.py
│   ├── generate.py                   # Synthetic data generator
│   ├── seed_local.py                 # Local seed data
│   └── upload.py                     # Upload to DynamoDB
│
├── tests/                            # Test suite
│   ├── unit/                         # Unit tests
│   │   ├── test_anomaly_model.py
│   │   ├── test_anomaly_detector.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_priority_scorer.py
│   │   ├── test_recommender.py
│   │   ├── test_risk_predictor.py
│   │   ├── test_impact_simulator.py
│   │   ├── test_dynamodb_retry.py
│   │   └── test_e2e_demo.py
│   ├── property/                     # Property-based tests
│   │   └── (hypothesis test modules)
│   └── frontend/
│       └── AlertsPanel.test.tsx
│
├── .gitignore
├── Makefile                          # Build & deployment automation
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## 🔧 Development

### Code Style & Linting

**Python**:
```bash
# Format code with black
black backend/ tests/

# Type checking with mypy
mypy backend/ --ignore-missing-imports

# Lint with pylint
pylint backend/
```

**TypeScript**:
```bash
# Format with prettier (included in Tailwind)
npx prettier --write frontend/src

# Type checking
tsc --noEmit
```

### Adding New Endpoints

1. Create router file in `backend/app/routers/`
2. Define request/response schemas in `backend/app/schemas.py`
3. Include router in `backend/app/main.py`
4. Add tests in `tests/unit/`
5. Update API documentation (README)

### Adding New ML Models

1. Train model locally or externally
2. Serialize with joblib: `joblib.dump(model, "path/to/model.pkl")`
3. Place `.pkl` file in `backend/models/`
4. Create interface in `backend/models/` (e.g., `new_model.py`)
5. Import in relevant router module
6. Add tests for inference

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Commit with conventional commits
git commit -m "feat: add new recommendation model"
git commit -m "fix: resolve anomaly scoring edge case"
git commit -m "docs: update API documentation"

# Push and create PR
git push origin feature/your-feature-name
```

**Commit Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## 🤝 Contributing

We welcome contributions to AquaMind AI! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-idea`
3. **Make** your changes with descriptive commits
4. **Add** tests for new functionality
5. **Ensure** all tests pass: `pytest` & `npm test`
6. **Submit** a Pull Request with a clear description

### Guidelines

- Follow PEP 8 (Python) and ESLint/Prettier (TypeScript) standards
- Write docstrings for all public functions/classes
- Include unit tests for >80% code coverage
- Keep commits atomic and well-described
- Update documentation for user-facing changes

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Darshan P Pawar**

- 🔗 GitHub: [@DarshanPawar7](https://github.com/DarshanPawar7)
- 📧 Email: [darshanpawarworks@email.com](mailto:darshanpawarworks@email.com)
- 💼 LinkedIn: [Darshan P Pawar](https://linkedin.com/in/darshanpawar7)

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **AWS Lambda Python**: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
- **AWS SAM**: https://aws.amazon.com/serverless/sam/
- **React Hooks**: https://react.dev/reference/react/hooks
- **scikit-learn IsolationForest**: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- **Amazon Bedrock**: https://docs.aws.amazon.com/bedrock/

---

## 🙏 Acknowledgments

- Built with FastAPI, React, and AWS serverless technologies
- ML anomaly detection powered by scikit-learn
- AI recommendations via Amazon Bedrock (Claude 3)
- Inspired by water utility operations and predictive maintenance best practices

---

## 🐛 Issues & Support

Found a bug or have a question? Please [open an issue](https://github.com/DarshanPawar/AquaMindAI/issues) on GitHub.

For security vulnerabilities, please email security@aquamind.ai instead of using the issue tracker.

---

**Made with ❤️ for water infrastructure resilience.**
