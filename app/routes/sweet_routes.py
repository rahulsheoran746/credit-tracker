from fastapi import APIRouter
from app.services.sweet_service import get_all_sweets

router = APIRouter()

@router.get("/sweets")
def list_sweets():
    return get_all_sweets()
