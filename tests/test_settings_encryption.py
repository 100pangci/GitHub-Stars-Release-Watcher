"""Tests for encrypted settings storage."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Setting
from app.services.settings import get_setting, is_secret_set, set_setting


def _memory_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_set_secret_is_encrypted_in_db():
    """Test that secret=True stores encrypted value, not plaintext."""
    db = _memory_session()
    try:
        set_setting(db, "github_token", "ghp_secret_123", secret=True)
        db.commit()

        raw = db.query(Setting).filter(Setting.key == "github_token").first()
        assert raw is not None
        # Should be encrypted (Fernet token), not plaintext
        assert raw.value != "ghp_secret_123"
        assert raw.value.startswith("gAAAAA")
        assert raw.secret is True
    finally:
        db.close()


def test_get_setting_decrypts_secret():
    """Test that get_setting decrypts stored secrets transparently."""
    db = _memory_session()
    try:
        set_setting(db, "github_token", "ghp_secret_456", secret=True)
        db.commit()

        value = get_setting(db, "github_token", "")
        assert value == "ghp_secret_456"
    finally:
        db.close()


def test_non_secret_is_not_encrypted():
    """Test that non-secret settings are stored as plaintext."""
    db = _memory_session()
    try:
        set_setting(db, "check_schedule", "weekly")
        db.commit()

        raw = db.query(Setting).filter(Setting.key == "check_schedule").first()
        assert raw is not None
        assert raw.value == "weekly"
        assert raw.secret is False
    finally:
        db.close()


def test_is_secret_set_works_with_encrypted():
    """Test is_secret_set returns True for encrypted non-empty values."""
    db = _memory_session()
    try:
        set_setting(db, "smtp_password", "smtp_pass", secret=True)
        db.commit()
        assert is_secret_set(db, "smtp_password") is True
    finally:
        db.close()


def test_is_secret_set_empty_returns_false():
    """Test is_secret_set returns False when no value is set."""
    db = _memory_session()
    try:
        assert is_secret_set(db, "nonexistent_key") is False
    finally:
        db.close()


def test_get_setting_missing_returns_default():
    """Test that get_setting returns the default for missing keys."""
    db = _memory_session()
    try:
        assert get_setting(db, "missing_key", "fallback") == "fallback"
    finally:
        db.close()


def test_set_setting_empty_deletes():
    """Test that set_setting with empty string deletes the row."""
    db = _memory_session()
    try:
        set_setting(db, "temp_key", "value")
        db.commit()
        assert get_setting(db, "temp_key", "") == "value"

        set_setting(db, "temp_key", "")
        db.commit()
        assert get_setting(db, "temp_key", "default") == "default"
    finally:
        db.close()
