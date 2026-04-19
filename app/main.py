import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import member_routes, transaction_routes, product_routes
from app.db import init_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield


app = FastAPI(title="Credit Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_routes.router)
app.include_router(member_routes.router)
app.include_router(transaction_routes.router)


@app.get("/")
def read_root():
    return {"message": "Sweet Shop API is Running"}
