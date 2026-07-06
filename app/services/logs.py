"""Application logging service."""

import logging
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import AppLog

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure application logging to stdout and DB."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root_logger.addHandler(handler)

    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def add_log(level: str, message: str, db: Session = None):
    """Add an application log entry."""
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        log = AppLog(
            level=level.upper(),
            message=str(message),
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        if should_close:
            db.commit()
    except Exception as e:
        if should_close:
            db.rollback()
        # Fallback to Python logger if DB fails
        logger.error(f"Failed to write app log: {e}")
    finally:
        if should_close:
            db.close()


def get_recent_logs(db: Session, limit: int = 200) -> list:
    """Get the most recent log entries."""
    return (
        db.query(AppLog)
        .order_by(AppLog.id.desc())
        .limit(limit)
        .all()
    )


def cleanup_old_logs(db: Session, keep_days: int = 30):
    """Delete log entries older than keep_days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    deleted = db.query(AppLog).filter(AppLog.created_at < cutoff).delete()
    if deleted:
        logger.info(f"Cleaned up {deleted} old log entries")