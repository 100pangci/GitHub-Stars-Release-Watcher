"""Encryption utilities for secret settings at rest."""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)

_KEY_CACHE: bytes | None = None


def _derive_key() -> bytes:
    """Derive a 32-byte Fernet key from the session secret via PBKDF2."""
    global _KEY_CACHE
    if _KEY_CACHE is not None:
        return _KEY_CACHE
    secret = settings.get_session_secret()
    raw = hashlib.pbkdf2_hmac("sha256", secret.encode(), b"gsrw-encryption", 100_000, dklen=32)
    _KEY_CACHE = base64.urlsafe_b64encode(raw)
    return _KEY_CACHE


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns a Fernet token."""
    f = Fernet(_derive_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet token. Raises InvalidToken on failure."""
    f = Fernet(_derive_key())
    return f.decrypt(ciphertext.encode()).decode()


def migrate_secrets_from_db():
    """Encrypt any secret settings that are still stored in plaintext.
    Safe to call on every startup — skips already-encrypted values."""
    from app.database import SessionLocal
    from app.models import Setting

    db = SessionLocal()
    try:
        secrets = db.query(Setting).filter(Setting.secret == True).all()  # noqa: E712
        for s in secrets:
            if s.value and not s.value.startswith("gAAAAA"):
                try:
                    s.value = encrypt(s.value)
                except Exception as e:
                    logger.warning("Failed to encrypt setting '%s': %s", s.key, e)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
