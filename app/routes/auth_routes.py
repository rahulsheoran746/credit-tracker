from fastapi import APIRouter, Depends, HTTPException
from app.auth.security import create_access_token
from app.auth.deps import get_current_user
from app.auth import rate_limit
from app.schemas.user_schema import LoginRequest, ChangePasswordRequest
from app.services.user_service import UserService
from app.services.audit_service import log_action
from app.db import get_connection

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(req: LoginRequest, conn=Depends(get_connection)):
    rl_key = f"login:{req.username.lower().strip()}"

    # Brute-force defence: block further attempts once the window cap is hit.
    allowed, retry_after = rate_limit.check(rl_key)
    if not allowed:
        log_action(conn, None, "login_rate_limited", "user", None, {"username": req.username})
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    user = UserService(conn).authenticate(req.username, req.password)
    if not user:
        rate_limit.register_failure(rl_key)
        log_action(conn, None, "login_failed", "user", None, {"username": req.username})
        raise HTTPException(status_code=401, detail="Invalid username or password")

    rate_limit.clear(rl_key)
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
