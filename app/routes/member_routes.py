from fastapi import APIRouter, Depends, HTTPException, Query
from ..schemas.member_schema import MemberCreate
from ..services.member_service import create_or_get_member, search_members, get_all_members
from ..db import get_connection

router = APIRouter()


@router.get("/members/search")
def search_members_route(q: str = Query(..., min_length=1), conn=Depends(get_connection)):
    try:
        return search_members(conn, q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/members")
def list_members(conn=Depends(get_connection)):
    try:
        return get_all_members(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/members")
def add_or_get_member(member: MemberCreate, conn=Depends(get_connection)):
    try:
        return create_or_get_member(conn, member)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
