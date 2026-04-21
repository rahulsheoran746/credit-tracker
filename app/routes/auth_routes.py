from fastapi import APIRouter, Depends, HTTPException
from app.auth.security import create_access_token
from app.auth.deps import get_current_user
from app.schemas.user_schema import LoginRequest, ChangePasswordRequest
from app.services.user_service import UserService
from app.services.audit_service import log_action
from app.db import get_connection

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(req: LoginRequest, conn=Depends(get_connection)):
    user = UserService(conn).authenticate(req.username, req.password)
    if not user:
        # Log the failed attempt with the submitted username
        log_action(conn, None, "login_failed", "user", None, {"username": req.username})
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user["id"], user["username"], user["role"])
    log_action(conn, user, "login", "user", user["id"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    user=Depends(get_current_user),
    conn=Depends(get_connection),
):
    try:
        UserService(conn).change_own_password(user["id"], req.current_password, req.new_password)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    log_action(conn, user, "update", "user", user["id"], {"field": "password"})
    return {"status": "ok"}
