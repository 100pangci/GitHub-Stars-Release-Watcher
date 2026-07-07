"""Authentication and security utilities."""

import logging
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings
from app.database import SessionLocal
from app.services.settings import get_setting, set_setting

logger = logging.getLogger(__name__)

# Session cookie name
SESSION_COOKIE = "gsrw_session"
SESSION_MAX_AGE = 7 * 24 * 3600  # 7 days in seconds

_serializer: URLSafeTimedSerializer | None = None


def get_serializer() -> URLSafeTimedSerializer:
    """Get or create the serializer for session tokens."""
    global _serializer
    if _serializer is None:
        secret = settings.get_session_secret()
        _serializer = URLSafeTimedSerializer(secret, salt="session")
    return _serializer


def reset_serializer():
    """Force the serializer to re-initialize with the current session_secret."""
    global _serializer
    _serializer = None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly (bypasses passlib compatibility issue)."""
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    import bcrypt as _bcrypt
    try:
        return _bcrypt.checkpw(password.encode(), hashed.encode())
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


def ensure_session_secret():
    """Persist the session secret to DB in plaintext so it survives restarts.

    Stored unencrypted on purpose — encrypting a key with itself creates a
    circular dependency that breaks on every restart.

    When an old encrypted Fernet token (gAAAAA...) is found, we decrypt it
    using the current in-memory session secret (which auto-generates if
    unset). Within the same process the decryption succeeds; on restart the
    old token can't be decrypted by a freshly-generated secret, so a new
    secret is generated and persisted — this invalidates existing sessions
    and re-encrypts the password hash on the first affected restart.
    """
    global _serializer
    db = SessionLocal()
    try:
        from app.models import Setting
        row = db.query(Setting).filter(Setting.key == "session_secret").first()

        if row and row.value:
            if row.value.startswith("gAAAAA"):
                from app.crypto import decrypt as _crypto_decrypt
                try:
                    old_plain = _crypto_decrypt(row.value)
                    settings.session_secret = old_plain
                    row.value = old_plain
                    row.secret = False
                    db.commit()
                    logger.info("Migrated old encrypted session_secret to plaintext")
                    _serializer = None
                    return
                except Exception:
                    pass
            else:
                settings.session_secret = row.value
                return

        new_secret = settings.get_session_secret()
        settings.session_secret = new_secret

        if row:
            row.value = new_secret
            row.secret = False
        else:
            db.add(Setting(key="session_secret", value=new_secret, secret=False))
        db.commit()
        logger.info("Generated new session secret")
        _serializer = None
    except Exception:
        db.rollback()
    finally:
        db.close()


def ensure_password_configured():
    """Set initial password if not configured, using env var if provided."""
    if is_password_configured():
        return None

    plain_password = settings.app_password or secrets.token_urlsafe(16)
    hashed = hash_password(plain_password)
    set_stored_password_hash(hashed)

    if settings.app_password:
        logger.info("Password set from APP_PASSWORD environment variable")
    else:
        print("\n" + "=" * 60)
        print("INITIAL PASSWORD GENERATED (first run):")
        print(f"  Password: {plain_password}")
        print("=" * 60 + "\n")

    return None


def create_session(response: Response, secure: bool | None = None) -> str:
    """Create a new session and set the cookie.

    Args:
        response: The response to set the cookie on.
        secure: Whether the cookie should have the Secure flag.
                If None, uses settings.app_cookie_secure.
    """
    serializer = get_serializer()
    token = serializer.dumps({"created": datetime.now(UTC).timestamp()})
    if secure is None:
        secure = settings.app_cookie_secure
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=secure,
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
            if request.url.path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="Unauthorized")
            return RedirectResponse(url="/login", status_code=303)


login_required = LoginRequired()
