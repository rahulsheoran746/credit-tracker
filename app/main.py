from fastapi import FastAPI
from app.routes import member_routes, transaction_routes, sweet_routes

app = FastAPI()

app.include_router(member_routes.router)
app.include_router(transaction_routes.router)
app.include_router(sweet_routes.router)

@app.get("/")
def read_root():
    return {"message": "Sweet Shop API is Running ✅"}
