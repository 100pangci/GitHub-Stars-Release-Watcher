"""Authentication router - login, logout, change password."""

import secrets
import time

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import SessionLocal
from app.security import (
    create_session,
    destroy_session,
    get_serializer,
    get_stored_password_hash,
    hash_password,
    set_stored_password_hash,
    validate_session,
    verify_password,
)
from app.services.settings import set_setting

router = APIRouter()

# In-memory rate limiting for login attempts
_login_attempts: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 900  # 15 minutes
RATE_LIMIT_MAX = 5


def _check_rate_limit(ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    if len(attempts) >= RATE_LIMIT_MAX:
        return False
    attempts.append(now)
    _login_attempts[ip] = attempts
    return True


@router.post("/login")
async def login(
    request: Request,
    password: str = Form(...),
):
    """Process login."""
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        return JSONResponse(
            {"success": False, "message": "Too many login attempts. Try again in 15 minutes."},
            status_code=429,
        )

    stored_hash = get_stored_password_hash()
    if not stored_hash or not verify_password(password, stored_hash):
        return JSONResponse({"success": False, "message": "Invalid password"}, status_code=401)

    is_https = request.url.scheme == "https"
    response = JSONResponse({"success": True, "message": "Login successful"})
    create_session(response, secure=is_https)
    return response


@router.post("/logout")
async def logout():
    """Logout and destroy session."""
    response = JSONResponse({"success": True, "message": "Logged out"})
    destroy_session(response)
    return response


@router.post("/api/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
):
    """Change the web login password."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    stored_hash = get_stored_password_hash()
    if not stored_hash or not verify_password(current_password, stored_hash):
        return JSONResponse(
            {"success": False, "message": "Current password is incorrect"},
            status_code=400,
        )

    if len(new_password) < 8:
        return JSONResponse(
            {"success": False, "message": "New password must be at least 8 characters"},
            status_code=400,
        )

    set_stored_password_hash(hash_password(new_password))

    # Invalidate all existing sessions by regenerating the session secret
    db = SessionLocal()
    try:
        new_secret = secrets.token_hex(32)
        settings.session_secret = new_secret
        set_setting(db, "session_secret", new_secret, secret=False)
        db.commit()
        from app.security import reset_serializer
        reset_serializer()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return JSONResponse({"success": True, "message": "Password changed successfully"})
