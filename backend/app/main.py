"""FastAPI application entry point for AquaMind AI API."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from backend.app.routers import alerts, detect, explain, pipes, seed, simulate, whatif

app = FastAPI(title="AquaMind AI API")

# ---------------------------------------------------------------------------
# CORS — must be added BEFORE exception handlers so headers are always present
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler — ensures CORS headers survive unhandled errors
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error_message": "Internal server error", "request_id": request_id},
        headers={"Access-Control-Allow-Origin": "*"},
    )

# ---------------------------------------------------------------------------
# Structured request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "endpoint": str(request.url.path),
        "response_status_code": response.status_code,
    }
    print(json.dumps(log_entry), flush=True)

    return response

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(simulate.router)
app.include_router(seed.router)
app.include_router(pipes.router)
app.include_router(alerts.router)
app.include_router(detect.router)
app.include_router(whatif.router)
app.include_router(explain.router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Mangum adapter (AWS Lambda handler)
# ---------------------------------------------------------------------------
handler = Mangum(app)
