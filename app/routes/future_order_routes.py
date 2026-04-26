from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.future_order_schema import (
    FutureOrderCreate, FutureOrderFulfill, FutureOrderCancel,
)
from app.services.future_order_service import FutureOrderService
from app.services.audit_service import log_action
from app.auth.deps import get_current_user
from app.db import get_connection

router = APIRouter()


@router.get("/future-orders")
def list_future_orders(
    status: str | None = Query(None, description="pending | fulfilled | cancelled"),
    pickup_from: date | None = Query(None),
    pickup_to:   date | None = Query(None),
    member_id:   int  | None = Query(None),
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    return FutureOrderService(conn).list_orders(
        status=status, pickup_from=pickup_from,
        pickup_to=pickup_to, member_id=member_id,
    )


@router.get("/future-orders/{order_id}")
def get_future_order(order_id: int,
                     user=Depends(get_current_user),
                     conn=Depends(get_connection)):
    order = FutureOrderService(conn).get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Future order not found")
    return order


@router.post("/future-orders", status_code=201)
def create_future_order(
    payload: FutureOrderCreate,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = FutureOrderService(conn).create_order(payload.model_dump(mode="json"))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    log_action(conn, user, "create", "future_order", result["id"], {
        "member_id": payload.member_id,
        "pickup_date": str(payload.pickup_date),
        "items": len(payload.items),
        "token_cash": payload.token_cash,
        "token_upi":  payload.token_upi,
    })
    return result


@router.post("/future-orders/{order_id}/fulfill", status_code=201)
def fulfill_future_order(
    order_id: int,
    payload: FutureOrderFulfill,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = FutureOrderService(conn).fulfill_order(order_id, payload.model_dump(mode="json"))
        if not result:
            raise HTTPException(status_code=404, detail="Future order not found")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    log_action(conn, user, "fulfill", "future_order", order_id, {
        "transaction_id": result.get("fulfilled_transaction_id"),
        "items_total": result.get("items_total"),
        "refund_due": result.get("refund_due"),
    })
    return result


@router.post("/future-orders/{order_id}/cancel")
def cancel_future_order(
    order_id: int,
    payload: FutureOrderCancel,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = FutureOrderService(conn).cancel_order(order_id, payload.reason)
        if not result:
            raise HTTPException(status_code=404, detail="Future order not found")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    log_action(conn, user, "cancel", "future_order", order_id, {
        "reason": payload.reason,
        "refund_due": result.get("refund_due"),
    })
    return result
