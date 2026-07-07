"""Base class for all notification channels."""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session


class BaseNotifier(ABC):
    """Abstract base for a notification channel (email, webhook, etc.)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier, e.g. 'email' or 'webhook'."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable label shown in the UI, e.g. 'Email (SMTP)'."""
        ...

    @abstractmethod
    def is_configured(self, db: Session) -> bool:
        """Return True if this notifier has enough settings to send."""
        ...

    @abstractmethod
    def get_settings(self, db: Session) -> dict[str, Any]:
        """Return current settings dict for this notifier."""
        ...

    @abstractmethod
    def save_settings(self, db: Session, data: dict[str, str]) -> None:
        """Persist settings from the API form data. Commit inside."""
        ...

    def send_test(self, db: Session) -> dict[str, Any]:
        """Send a test notification. Return {'success': bool, 'message': str}."""
        raise NotImplementedError

    def send_weekly_summary(self, db: Session, events: list | None = None) -> dict[str, Any]:
        """Send a weekly summary. Return {'sent': bool, 'message': str, 'updates': int}.

        If events is None the notifier should query for un-reported events itself.
        """
        raise NotImplementedError
