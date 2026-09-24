from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models import RoleEnum, User
from app.schemas import ChangePasswordRequest, LoginRequest, TokenResponse
from app.services.activity_log import log_activity
from app.utils.rate_limit import limiter

logger = logging.getLogger("auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
COOKIE_NAME = "access_token"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    generic_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="نام کاربری یا رمز عبور اشتباه است.")

    if not user or not user.is_active:
        logger.info("Failed login attempt for unknown/inactive username")
        raise generic_error

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"به دلیل تلاش‌های ناموفق زیاد، حساب موقتاً قفل شده. لطفاً {remaining} دقیقه دیگر تلاش کنید.",
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_login_attempts = 0
        db.commit()
        log_activity(db, None, "login_failed", details=f"username={username}", ip_address=request.client.host if request.client else None)
        raise generic_error

    # success
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role.value})
    log_activity(db, user, "login_success", ip_address=request.client.host if request.client else None)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.session_expire_minutes * 60,
        path="/",
    )

    return TokenResponse(access_token=token, role=user.role.value, display_name=user.display_name)


@router.post("/logout")
def logout(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_activity(db, user, "logout")
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "خارج شدید."}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="رمز عبور فعلی اشتباه است.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    log_activity(db, user, "password_changed")
