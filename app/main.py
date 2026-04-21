import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    member_routes, transaction_routes, product_routes, loan_routes,
    auth_routes, user_routes,
)
from app.db import init_pool, get_connection_sync
from app.services.user_service import bootstrap_admin_if_empty
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    # Ensure at least one admin exists so you can log in the first time
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
