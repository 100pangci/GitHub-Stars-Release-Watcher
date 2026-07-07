"""Notifier framework — pluggable notification channels."""

from app.services.notifiers.base import BaseNotifier
from app.services.notifiers.email import EmailNotifier

__all__ = ["BaseNotifier", "EmailNotifier"]
