from fastapi import APIRouter, Depends, HTTPException
from app.schemas.sweet_schema import SweetCreate, SweetUpdate
from app.services.sweet_service import SweetService
from app.db import get_connection

router = APIRouter()


@router.get("/sweets")
def list_sweets(conn=Depends(get_connection)):
    return SweetService(conn).get_all_sweets()


@router.post("/sweets", status_code=201)
def create_sweet(sweet: SweetCreate, conn=Depends(get_connection)):
    try:
        return SweetService(conn).create_sweet(sweet.name, sweet.rate_per_kg, sweet.description)
    except Exception as e:
        if 'unique' in str(e).lower():
            raise HTTPException(status_code=409, detail="A sweet with this name already exists.")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sweets/{sweet_id}")
def update_sweet(sweet_id: int, sweet: SweetUpdate, conn=Depends(get_connection)):
    try:
        result = SweetService(conn).update_sweet(sweet_id, sweet.rate_per_kg, sweet.description)
        if not result:
            raise HTTPException(status_code=404, detail="Sweet not found.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sweets/{sweet_id}/calculate-amount")
def calculate_amount(sweet_id: int, quantity: float, conn=Depends(get_connection)):
    sweet = SweetService(conn).get_sweet_by_id(sweet_id)
    if not sweet:
        raise HTTPException(status_code=404, detail="Sweet not found")
    return {"sweet_id": sweet_id, "quantity": quantity,
            "rate_per_kg": sweet["rate_per_kg"],
            "amount": round(sweet["rate_per_kg"] * quantity, 2)}


@router.get("/sweets/{sweet_id}/calculate-quantity")
def calculate_quantity(sweet_id: int, amount: float, conn=Depends(get_connection)):
    sweet = SweetService(conn).get_sweet_by_id(sweet_id)
    if not sweet or sweet["rate_per_kg"] == 0:
        raise HTTPException(status_code=404, detail="Sweet not found or price invalid")
    return {"sweet_id": sweet_id, "amount": amount,
            "quantity": round(amount / sweet["rate_per_kg"], 2)}
