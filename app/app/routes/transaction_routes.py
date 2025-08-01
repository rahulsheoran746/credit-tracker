from fastapi import APIRouter, Depends, HTTPException
from app.schemas.transaction_schema import TransactionPayload, MemberQuery, MemberTransactionsResponse
from app.db import get_connection
from app.services.transaction_service import TransactionService

router = APIRouter()

@router.post("/transactions/")
def process_transaction(payload: TransactionPayload, conn=Depends(get_connection)):
    service = TransactionService(conn)
    result = service.process_transaction_payload(payload.dict())
    return result

@router.post("/member/transactions", response_model=MemberTransactionsResponse)
def read_member_transactions(member: MemberQuery, conn=Depends(get_connection)):
    service = TransactionService(conn)
    data = service.get_member_transactions(member)
    if data is None:
        raise HTTPException(status_code=404, detail="Member not found or no transactions available")
    return data
