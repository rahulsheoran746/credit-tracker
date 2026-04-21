import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    member_routes, transaction_routes, product_routes, loan_routes,
    auth_routes, user_routes,
)
from app.db import init_pool, get_connection_sync
from app.services.user_service import bootstrap_admin_if_empty
from app.auth.security import JWT_SECRET

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


def _check_production_env() -> None:
    """
    Refuse to boot with unsafe defaults in production. Specifically:
    JWT_SECRET must be set to something that isn't the placeholder.

    Opt out via ALLOW_UNSAFE_DEFAULTS=1 for throwaway test setups.
    """
    if os.getenv("ALLOW_UNSAFE_DEFAULTS") == "1":
        return
    if JWT_SECRET == "CHANGE_ME_IN_PRODUCTION":
        logger.critical(
            "Refusing to start: JWT_SECRET is set to the placeholder value. "
            "Generate a fresh secret and set it in your .env file:\n"
            "    python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
        sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_env()
    init_pool()
    try:
        conn = get_connection_sync()
        bootstrap_admin_if_empty(conn)
        conn.close()
    except Exception:
        logging.exception("Admin bootstrap failed (continuing)")
    yield


app = FastAPI(title="Credit Tracker API", lifespan=lifespan)

_allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:4173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes — unauthenticated (must be first so login works)
app.include_router(auth_routes.router)

# Protected feature routes
app.include_router(product_routes.router)
app.include_router(member_routes.router)
app.include_router(transaction_routes.router)
app.include_router(loan_routes.router)

# Admin-only
app.include_router(user_routes.router)


@app.get("/")
def read_root():
    return {"message": "Credit Tracker API is running"}


@app.get("/health")
def health():
    """
    Uptime-monitor endpoint. Verifies the process is running AND the DB is reachable.
    Returns 200 with {"status":"ok"} on success; 503 otherwise.
    """
    try:
        conn = get_connection_sync()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail=f"db-unreachable: {e}")
    return {"status": "ok"}
