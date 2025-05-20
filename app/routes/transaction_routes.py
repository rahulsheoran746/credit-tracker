from fastapi import APIRouter
from app.models.transaction import TransactionCreate
from app.services.transaction_service import create_sweet_transaction_service

router = APIRouter()

@router.post("/transactions/sweets")
def create_sweets_transaction(transaction: TransactionCreate):
    return create_sweet_transaction_service(transaction)
