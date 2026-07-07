"""Legacy backward-compat wrapper — delegates to EmailNotifier.

New code should import from ``app.services.notifiers.email`` or use
the ``app.services.notifier_manager.manager`` singleton directly.
"""

import logging
import warnings

from app.database import SessionLocal
from app.services.notifiers.email import EmailNotifier

logger = logging.getLogger(__name__)
_notifier = EmailNotifier()


def get_smtp_config(db):
    warnings.warn("Use EmailNotifier._config() directly", DeprecationWarning, stacklevel=2)
    return _notifier._config(db)


def is_email_configured(db):
    return _notifier.is_configured(db)


def send_test_email(db):
    result = _notifier.send_test(db)
    if result["success"]:
        return result["message"]
    raise ValueError(result["message"])


def send_weekly_summary(db):
    return _notifier.send_weekly_summary(db)
