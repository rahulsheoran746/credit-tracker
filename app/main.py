import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import member_routes, transaction_routes, sweet_routes
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

app.include_router(sweet_routes.router)
app.include_router(member_routes.router)
app.include_router(transaction_routes.router)


@app.get("/")
def read_root():
    return {"message": "Sweet Shop API is Running"}
