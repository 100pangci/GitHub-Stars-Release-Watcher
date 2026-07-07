"""Central registry for notification channels.

Usage
-----
    from app.services.notifier_manager import manager
    from app.services.notifiers.email import EmailNotifier

    manager.register(EmailNotifier)

    for n in manager.get_configured(db):
        n.send_weekly_summary(db)
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.models import Event
from app.services.settings import get_setting
from app.services.logs import add_log

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.services.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class NotifierManager:
    """Singleton registry that holds all available notifier *classes*."""

    def __init__(self):
        self._classes: dict[str, type["BaseNotifier"]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, cls: type["BaseNotifier"]) -> None:
        inst = cls()
        key = inst.name
        if key in self._classes:
            logger.warning("Overwriting existing notifier '%s'", key)
        self._classes[key] = cls
        logger.debug("Registered notifier: %s (%s)", key, inst.display_name)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> "BaseNotifier | None":
        cls = self._classes.get(name)
        return cls() if cls else None

    def get_all(self) -> list["BaseNotifier"]:
        return [cls() for cls in self._classes.values()]

    def get_configured(self, db: "Session") -> list["BaseNotifier"]:
        return [n for n in self.get_all() if n.is_configured(db)]

    # ------------------------------------------------------------------
    # Bulk actions
    # ------------------------------------------------------------------

    def send_all_weekly_summaries(self, db: "Session") -> dict[str, dict]:
        """Query un-reported events once and dispatch to every configured notifier.

        Returns a dict keyed by notifier name, e.g. ``{"email": {"sent": True, …}}``.
        """
        results: dict[str, dict] = {}

        configured = self.get_configured(db)
        if not configured:
            msg = "Weekly summary skipped: no notification channels configured"
            add_log("WARNING", msg, db=db)
            logger.warning(msg)
            return {}

        # Shared: query events once
        week_ago = datetime.now(UTC) - timedelta(days=7)
        events = (
            db.query(Event)
            .filter(
                Event.created_at >= week_ago,
                Event.included_in_weekly_summary == False,  # noqa: E712
            )
            .order_by(Event.created_at.desc())
            .all()
        )

        total = len(events)

        # Mark events as included before dispatching
        for evt in events:
            evt.included_in_weekly_summary = True
        db.commit()

        for notifier in configured:
            try:
                result = notifier.send_weekly_summary(db, events)
                results[notifier.name] = result
            except Exception as e:
                logger.exception("Notifier '%s' failed during weekly summary", notifier.name)
                results[notifier.name] = {"sent": False, "message": str(e), "updates": total}

        return results


# Module-level singleton
manager = NotifierManager()
