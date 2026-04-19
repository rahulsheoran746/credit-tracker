from fastapi import APIRouter, Depends, HTTPException
from ..schemas.member_schema import MemberCreate
from ..services.member_service import create_or_get_member
from ..db import get_connection

router = APIRouter()


@router.post("/members")
def add_or_get_member(member: MemberCreate, conn=Depends(get_connection)):
    try:
        return create_or_get_member(conn, member)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
