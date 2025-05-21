from fastapi import APIRouter,  Depends, HTTPException
from app.services.sweet_service import SweetService
from app.db import get_connection
router = APIRouter()

@router.get("/sweets")
def list_sweets(conn=Depends(get_connection)):
    sweet_service = SweetService(conn)
    return sweet_service.get_all_sweets()

@router.get("/sweets/{sweet_id}/calculate-amount")
def calculate_amount(sweet_id: int, quantity: float, conn=Depends(get_connection)):
    sweet_service = SweetService(conn)
    sweet = sweet_service.get_sweet_by_id(sweet_id)
    if not sweet:
        raise HTTPException(status_code=404, detail="Sweet not found")

    amount = float(sweet["rate_per_kg"]) * quantity
    return {
        "sweet_id": sweet_id,
        "quantity": quantity,
        "rate_per_kg": float(sweet["rate_per_kg"]),
        "amount": round(amount, 2)
    }


@router.get("/sweets/{sweet_id}/calculate-quantity")
def calculate_quantity(sweet_id: int, amount: float, conn=Depends(get_connection)):
    sweet_service = SweetService(conn)
    sweet = sweet_service.get_sweet_by_id(sweet_id)
    if not sweet or float(sweet['rate_per_kg']) == 0:
        raise HTTPException(status_code=404, detail="Sweet not found or price invalid")
    quantity = amount / float(sweet['rate_per_kg'])
    return {
        "sweet_id": sweet_id,
        "amount": amount,
        "quantity": round(quantity, 2)
    }
