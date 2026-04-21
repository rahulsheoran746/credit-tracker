from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth.deps import require_admin
from app.schemas.user_schema import UserCreate, UserUpdate, UserResetPassword
from app.services.user_service import UserService
from app.services.audit_service import log_action
from app.db import get_connection

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(
    include_inactive: bool = Query(False),
    admin=Depends(require_admin),
    conn=Depends(get_connection),
):
    return UserService(conn).list_users(include_inactive=include_inactive)


@router.post("", status_code=201)
def create_user(
    data: UserCreate,
    admin=Depends(require_admin),
    conn=Depends(get_connection),
):
    try:
        user = UserService(conn).create(
            data.username, data.name, data.phone, data.role, data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    log_action(conn, admin, "create", "user", user["id"], {"username": user["username"], "role": user["role"]})
    return user


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    admin=Depends(require_admin),
    conn=Depends(get_connection),
):
    # Don't let an admin deactivate themselves (avoids locking yourself out)
    if data.is_active is False and user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    try:
        user = UserService(conn).update(
            user_id,
            name=data.name, phone=data.phone, role=data.role, is_active=data.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    log_action(conn, admin, "update", "user", user_id, data.model_dump(exclude_none=True))
    return user


@router.post("/{user_id}/reset-password", status_code=200)
def reset_password(
    user_id: int,
    data: UserResetPassword,
    admin=Depends(require_admin),
    conn=Depends(get_connection),
):
    try:
        ok = UserService(conn).reset_password(user_id, data.new_password, set_must_change=True)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    log_action(conn, admin, "update", "user", user_id, {"field": "password_reset_by_admin"})
    return {"status": "ok"}
