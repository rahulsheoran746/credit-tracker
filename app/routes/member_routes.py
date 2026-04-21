from fastapi import APIRouter, Depends, HTTPException, Query
from ..schemas.member_schema import MemberCreate, MemberUpdate
from ..services.member_service import (
    create_or_get_member, search_members, get_all_members, update_member,
)
from ..services.audit_service import log_action
from ..auth.deps import get_current_user
from ..db import get_connection

router = APIRouter()


@router.get("/members/search")
def search_members_route(
    q: str = Query(..., min_length=1),
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        return search_members(conn, q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/members")
def list_members(user=Depends(get_current_user), conn=Depends(get_connection)):
    try:
        return get_all_members(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/members")
def add_or_get_member(
    member: MemberCreate,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = create_or_get_member(conn, member)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if "New" in (result.get("message") or ""):
        log_action(conn, user, "create", "member", result["id"],
                   {"name": member.name, "phone": member.phone})
    return result


@router.put("/members/{member_id}")
def update_member_route(
    member_id: int,
    member: MemberUpdate,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        result = update_member(conn, member_id, member)
        if not result:
            raise HTTPException(status_code=404, detail="Member not found")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    log_action(conn, user, "update", "member", member_id, member.model_dump(exclude_none=True))
    return result
