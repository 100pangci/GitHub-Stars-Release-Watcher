"""APScheduler integration for background tasks."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import TaskRun
from app.services.logs import add_log
from app.services.settings import get_setting, set_setting

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None
_running_tasks: dict = {}  # task_name -> bool (lock)


async def run_task(task_name: str, task_func, **kwargs):
    """Run a background task with concurrency protection and status tracking."""
    # Check if already running
    if _running_tasks.get(task_name, False):
        logger.warning(f"Task '{task_name}' is already running, skipping")
        db = SessionLocal()
        try:
            run = TaskRun(
                task_name=task_name,
                status="skipped",
                message="Previous task still running",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )
            db.add(run)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        return

    _running_tasks[task_name] = True
    db = SessionLocal()
    task_run = None
    try:
        task_run = TaskRun(
            task_name=task_name,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(task_run)
        db.commit()
        db.refresh(task_run)

        result = await task_func(**kwargs)

        # Update run
        task_run.status = "completed"
        task_run.finished_at = datetime.now(timezone.utc)
        task_run.checked_repos = result.get("checked", result.get("synced", 0))
        task_run.found_updates = result.get("updates", result.get("new", 0))
        db.commit()

    except Exception as e:
        logger.exception(f"Task '{task_name}' failed: {e}")
        if task_run:
            task_run.status = "failed"
            task_run.finished_at = datetime.now(timezone.utc)
            task_run.message = str(e)[:500]
            db.commit()
    finally:
        _running_tasks[task_name] = False
        db.close()


async def sync_stars_job():
    """Scheduled job to sync stars."""
    from app.services.stars import sync_stars as _sync_stars
    db = SessionLocal()
    try:
        username = get_setting(db, "github_username", "")
        token = get_setting(db, "github_token", "")
        delay = float(get_setting(db, "github_request_delay", "0.2"))
    finally:
        db.close()

    if not username or not token:
        logger.warning("GitHub username or token not configured, skipping sync")
        return

    await run_task("sync_stars", _sync_stars, username=username, token=token, delay=delay)


async def check_releases_job():
    """Scheduled job to check releases."""
    from app.services.releases import check_releases as _check_releases
    db = SessionLocal()
    try:
        token = get_setting(db, "github_token", "")
        delay = float(get_setting(db, "github_request_delay", "0.2"))
    finally:
        db.close()

    if not token:
        logger.warning("GitHub token not configured, skipping release check")
        return

    await run_task("check_releases", _check_releases, token=token, delay=delay)


async def weekly_summary_job():
    """Scheduled job to send weekly summary."""
    from app.services.emailer import send_weekly_summary
    db = SessionLocal()
    try:
        send_weekly_summary(db)
    finally:
        db.close()


async def cleanup_logs_job():
    """Scheduled job to clean up old logs."""
    db = SessionLocal()
    try:
        from app.services.logs import cleanup_old_logs
        cleanup_old_logs(db)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def init_scheduler():
    """Initialize and configure the APScheduler based on settings."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)

    scheduler = AsyncIOScheduler(timezone="utc")

    # Read schedule settings
    db = SessionLocal()
    try:
        schedule = get_setting(db, "check_schedule", "weekly")
        weekday = get_setting(db, "check_weekday", "mon")
        check_time = get_setting(db, "check_time", "09:00")
        custom_interval = get_setting(db, "custom_interval_minutes", "60")
    finally:
        db.close()

    # Add stars sync job (less frequently - every 6 hours)
    scheduler.add_job(
        sync_stars_job,
        IntervalTrigger(hours=6),
        id="sync_stars",
        name="Sync GitHub Stars",
        replace_existing=True,
    )

    # Add release check job based on schedule
    if schedule == "hourly":
        trigger = IntervalTrigger(hours=1)
    elif schedule == "daily":
        try:
            hour, minute = check_time.split(":", 1)
            trigger = CronTrigger(hour=int(hour), minute=int(minute))
        except (ValueError, IndexError):
            trigger = CronTrigger(hour=9, minute=0)
    elif schedule == "weekly":
        try:
            hour, minute = check_time.split(":", 1)
            weekday_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            day = weekday_map.get(weekday.lower(), 0)
            trigger = CronTrigger(day_of_week=day, hour=int(hour), minute=int(minute))
        except (ValueError, IndexError):
            trigger = CronTrigger(day_of_week=0, hour=9, minute=0)
    elif schedule == "custom":
        try:
            minutes = max(15, int(custom_interval))
            trigger = IntervalTrigger(minutes=minutes)
        except (ValueError, TypeError):
            trigger = IntervalTrigger(hours=24)
    else:
        # Default: weekly on Monday at 09:00
        trigger = CronTrigger(day_of_week=0, hour=9, minute=0)

    scheduler.add_job(
        check_releases_job,
        trigger,
        id="check_releases",
        name="Check Releases",
        replace_existing=True,
    )

    # Add weekly summary job (always weekly, on configured weekday/time)
    try:
        hour, minute = check_time.split(":", 1)
        weekday_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        day = weekday_map.get(weekday.lower(), 0)
        summary_trigger = CronTrigger(day_of_week=day, hour=int(hour), minute=int(minute))
    except (ValueError, IndexError):
        summary_trigger = CronTrigger(day_of_week=0, hour=9, minute=30)  # 30 min after check

    scheduler.add_job(
        weekly_summary_job,
        summary_trigger,
        id="weekly_summary",
        name="Weekly Summary Email",
        replace_existing=True,
    )

    # Add cleanup job (daily at 03:00)
    scheduler.add_job(
        cleanup_logs_job,
        CronTrigger(hour=3, minute=0),
        id="cleanup_logs",
        name="Cleanup Old Logs",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Task scheduler initialized")

    # Run initial sync if configured
    db = SessionLocal()
    try:
        username = get_setting(db, "github_username", "")
        token = get_setting(db, "github_token", "")
        if username and token:
            # Sync stars on startup (fire and forget)
            asyncio.ensure_future(sync_stars_job())
    finally:
        db.close()


def reload_scheduler():
    """Reload the scheduler (called when settings change)."""
    logger.info("Reloading scheduler due to settings change")
    init_scheduler()