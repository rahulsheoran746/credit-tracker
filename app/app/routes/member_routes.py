from fastapi import APIRouter, HTTPException
from ..schemas.member_schema import MemberCreate
from ..services.member_service import create_or_get_member

router = APIRouter()

@router.post("/members")
def add_or_get_member(member: MemberCreate):
    try:
        return create_or_get_member(member)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
