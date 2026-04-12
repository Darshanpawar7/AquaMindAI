.PHONY: build deploy simulate test test-frontend clean

# ── Configuration ──────────────────────────────────────────────────────────────
STACK_NAME   ?= aquamind-ai
REGION       ?= us-east-1
ENV          ?= prod
TABLE_PREFIX ?= aquamind

# Populated after first deploy (or set manually)
S3_BUCKET    ?=
CF_DIST_ID   ?=
API_URL      ?=

# ── Build ──────────────────────────────────────────────────────────────────────
build: build-backend build-frontend

build-backend:
	@echo "==> SAM build (backend)"
	sam build --template infra/template.yaml --config-file infra/samconfig.toml

build-frontend:
	@echo "==> React build (frontend)"
	npm install --prefix frontend
	npm run build --prefix frontend

# ── Deploy ─────────────────────────────────────────────────────────────────────
deploy: build-backend
	@echo "==> SAM deploy"
	sam deploy \
		--template infra/template.yaml \
		--config-file infra/samconfig.toml \
		--stack-name $(STACK_NAME) \
		--region $(REGION) \
		--parameter-overrides Environment=$(ENV) TablePrefix=$(TABLE_PREFIX)

deploy-frontend:
	@[ -n "$(S3_BUCKET)" ]   || (echo "ERROR: S3_BUCKET is not set"; exit 1)
	@[ -n "$(CF_DIST_ID)" ]  || (echo "ERROR: CF_DIST_ID is not set"; exit 1)
	@echo "==> Deploying frontend to S3 + CloudFront"
	bash frontend/deploy.sh $(S3_BUCKET) $(CF_DIST_ID) $(API_URL)

# ── Simulate ───────────────────────────────────────────────────────────────────
simulate:
	@echo "==> Running data simulator (uploads to DynamoDB)"
	TABLE_PREFIX=$(TABLE_PREFIX) python simulator/upload.py

simulate-dry:
	@echo "==> Dry-run simulator (no DynamoDB writes)"
	DRY_RUN=true TABLE_PREFIX=$(TABLE_PREFIX) python simulator/upload.py

# ── Tests ──────────────────────────────────────────────────────────────────────
test:
	@echo "==> Running Python unit tests"
	python -m pytest tests/unit/ -v

test-frontend:
	@echo "==> Running frontend Jest tests"
	npx jest --config frontend/jest.config.js

test-all: test test-frontend
	@echo "==> All tests complete"

# ── Utilities ──────────────────────────────────────────────────────────────────
clean:
	@echo "==> Cleaning build artifacts"
	rm -rf .aws-sam frontend/build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
