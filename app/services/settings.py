"""Settings management service."""

from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models import Setting


def get_setting(db: Session, key: str, default: Any = "") -> Any:
    """Get a setting value by key."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting is None:
        return default
    return setting.value


def set_setting(db: Session, key: str, value: str, secret: bool = False):
    """Set a setting value. If empty string, delete the setting."""
    if value == "":
        db.query(Setting).filter(Setting.key == key).delete()
        return
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


def get_all_settings(db: Session) -> dict:
    """Get all non-secret settings as a dict."""
    settings = db.query(Setting).all()
    result = {}
    for s in settings:
        if s.secret:
            result[s.key] = "***SET***" if s.value else ""
        else:
            result[s.key] = s.value
    return result


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
    import re
    return bool(re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', username))


def validate_interval_minutes(minutes: int) -> bool:
    """Validate check interval - minimum 15 minutes."""
    if not isinstance(minutes, int) or minutes < 15:
        return False
    return True