from fastapi import APIRouter, Depends, HTTPException
from app.schemas.transaction_schema import TransactionPayload, MemberQuery, MemberTransactionsResponse
from app.db import get_connection
from app.services.transaction_service import TransactionService
from app.services.audit_service import log_action
from app.auth.deps import get_current_user

router = APIRouter()


@router.post("/transactions/")
def process_transaction(
    payload: TransactionPayload,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        service = TransactionService(conn)
        result = service.process_transaction_payload(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Log summary of what was recorded
    first_block = payload.transactions[0] if payload.transactions else None
    log_action(conn, user, "create", "transaction", result.get("member_id"), {
        "type": first_block.type if first_block else None,
        "total_amount": first_block.total_amount if first_block else None,
        "amount_given": first_block.amount_given if first_block else None,
        "member_phone": payload.member.phone,
    })
    return result


@router.post("/member/transactions", response_model=MemberTransactionsResponse)
def read_member_transactions(
    member: MemberQuery,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        service = TransactionService(conn)
        data = service.get_member_transactions(member)
        if data is None:
            raise HTTPException(status_code=404, detail="Member not found or no transactions")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
