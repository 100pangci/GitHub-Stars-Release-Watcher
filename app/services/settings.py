"""Settings management service."""

import contextlib
import re
from typing import Any

from sqlalchemy.orm import Session

from app.crypto import decrypt, encrypt
from app.models import Setting


def get_setting(db: Session, key: str, default: Any = "") -> Any:
    """Get a setting value by key. Decrypts secret values transparently."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting is None:
        return default
    value = setting.value
    if setting.secret:
        with contextlib.suppress(Exception):
            value = decrypt(value)
    return value


def set_setting(db: Session, key: str, value: str, secret: bool = False):
    """Set a setting value. Encrypts when secret=True. Empty string deletes."""
    if value == "":
        db.query(Setting).filter(Setting.key == key).delete()
        return
    if secret:
        value = encrypt(value)
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
        if secret:
            setting.secret = True
    else:
        setting = Setting(key=key, value=value, secret=secret)
        db.add(setting)


def is_secret_set(db: Session, key: str) -> bool:
    """Check if a secret setting has a non-empty value (without revealing it)."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting is None:
        return False
    return bool(setting.value)


def validate_port(port_str: str) -> bool:
    """Validate SMTP port."""
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except (ValueError, TypeError):
        return False


def validate_github_username(username: str) -> bool:
    """Validate GitHub username - alphanumeric, hyphens, max 39 chars."""
    if not username or len(username) > 39:
        return False
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', username))



