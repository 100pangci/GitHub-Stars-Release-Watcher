"""Authentication and security utilities."""

import secrets
import logging
from datetime import timedelta, datetime, timezone
from functools import wraps
from typing import Optional

from fastapi import Request, HTTPException, Response
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import settings
from app.database import SessionLocal
from app.services.settings import get_setting, set_setting

logger = logging.getLogger(__name__)

# Session cookie name
SESSION_COOKIE = "gsrw_session"
SESSION_MAX_AGE = 7 * 24 * 3600  # 7 days in seconds

_serializer: Optional[URLSafeTimedSerializer] = None


def get_serializer() -> URLSafeTimedSerializer:
    """Get or create the serializer for session tokens."""
    global _serializer
    if _serializer is None:
        secret = settings.get_session_secret()
        _serializer = URLSafeTimedSerializer(secret, salt="session")
    return _serializer


def hash_password(password: str) -> str:
    """Hash a password using passlib bcrypt."""
    from passlib.hash import bcrypt
    return bcrypt.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    from passlib.hash import bcrypt
    try:
        return bcrypt.verify(password, hashed)
    except Exception:
        return False


def get_stored_password_hash() -> str:
    """Retrieve stored password hash from settings."""
    db = SessionLocal()
    try:
        return get_setting(db, "app_password_hash", default="")
    finally:
        db.close()


def set_stored_password_hash(password_hash: str):
    """Store password hash in settings."""
    db = SessionLocal()
    try:
        set_setting(db, "app_password_hash", password_hash, secret=True)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def is_password_configured() -> bool:
    """Check if a password has been configured."""
    return bool(get_stored_password_hash())


def ensure_password_configured():
    """Generate initial password if not configured. Returns the plain text password if newly generated."""
    if is_password_configured():
        return None

    # Generate a random password
    plain_password = secrets.token_urlsafe(16)
    hashed = hash_password(plain_password)
    set_stored_password_hash(hashed)

    logger.info("=" * 60)
    logger.info("INITIAL PASSWORD GENERATED (first run):")
    logger.info(f"  Password: {plain_password}")
    logger.info("=" * 60)

    # Also store in app_logs table for the Web UI logs page
    from app.models import AppLog
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        log = AppLog(
            level="INFO",
            message="Initial password generated. Check server startup logs for the password.",
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    # Print to stdout as well since the init happens during app startup
    print("\n" + "=" * 60)
    print("INITIAL PASSWORD GENERATED (first run):")
    print(f"  Password: {plain_password}")
    print("=" * 60 + "\n")

    return None  # Never return the plain password from this function on subsequent calls


def create_session(response: Response) -> str:
    """Create a new session and set the cookie."""
    serializer = get_serializer()
    token = serializer.dumps({"created": datetime.now(timezone.utc).timestamp()})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.app_cookie_secure,
        path="/",
    )
    return token


def destroy_session(response: Response):
    """Remove the session cookie."""
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.app_cookie_secure,
    )


def validate_session(request: Request) -> bool:
    """Check if the request has a valid session."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return False
    serializer = get_serializer()
    try:
        serializer.loads(token, max_age=SESSION_MAX_AGE)
        return True
    except (BadSignature, SignatureExpired):
        return False


class LoginRequired:
    """FastAPI dependency for protecting routes."""

    async def __call__(self, request: Request):
        if not validate_session(request):
            # For HTMX or API requests, return 401
            if request.headers.get("HX-Request") or request.url.path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="Unauthorized")
            # For regular page requests, redirect to login
            from fastapi.responses import RedirectResponse
            response = RedirectResponse(url="/login", status_code=303)
            raise HTTPException(status_code=303, detail="Redirecting to login", headers={"Location": "/login"})


login_required = LoginRequired()