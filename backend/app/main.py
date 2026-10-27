"""
TrustLens – FastAPI Application Entry Point
PROTOTYPE: Not an official AICTE system.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import applications, documents, findings, reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup + shutdown."""
    logger.info("TrustLens API starting up…")
    init_db()
    upload_dir = os.environ.get("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    logger.info("Database initialised. Upload directory ready: %s", upload_dir)
    yield
    logger.info("TrustLens API shutting down.")


app = FastAPI(
    title="TrustLens API",
    description=(
        "PROTOTYPE – Explainable AI Decision-Support for AICTE Application Scrutiny. "
        "NOT an official AICTE system. All findings are advisory only."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(findings.router, prefix="/api/findings", tags=["Findings"])
app.include_router(reports.router, prefix="/api/applications", tags=["Reports"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "TrustLens API"}


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please check server logs."},
    )
