"""APScheduler integration for background tasks."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models import TaskRun
from app.services.settings import get_setting

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None
_running_tasks: dict = {}  # task_name -> bool (lock)
_retry_tasks: dict = {}  # task_name -> retry_count


BACKOFF_DELAYS = [30, 60, 120, 240, 480]  # seconds
MAX_RETRIES = len(BACKOFF_DELAYS)


async def run_task(task_name: str, task_func, **kwargs) -> dict:
    """Run a background task with concurrency protection, status tracking, and auto-retry."""
    if _running_tasks.get(task_name, False):
        logger.warning(f"Task '{task_name}' is already running, skipping")
        db = SessionLocal()
        try:
            run = TaskRun(
                task_name=task_name,
                status="skipped",
                message="Previous task still running",
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
            )
            db.add(run)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        return {"skipped": True, "message": f"Task '{task_name}' is already running"}

    _running_tasks[task_name] = True
    db = SessionLocal()
    task_run = None
    try:
        task_run = TaskRun(
            task_name=task_name,
            status="running",
            started_at=datetime.now(UTC),
        )
        db.add(task_run)
        db.commit()
        db.refresh(task_run)

        result = await task_func(**kwargs)

        task_run.status = "completed"
        task_run.finished_at = datetime.now(UTC)
        task_run.checked_repos = result.get("checked", result.get("synced", 0))
        task_run.found_updates = result.get("updates", result.get("new", 0))
        db.commit()

        # Clear retry count on success
        _retry_tasks.pop(task_name, None)

        return result

    except Exception as e:
        logger.exception(f"Task '{task_name}' failed: {e}")
        if task_run:
            task_run.status = "failed"
            task_run.finished_at = datetime.now(UTC)
            task_run.message = str(e)[:500]
            db.commit()

        # Schedule retry with exponential backoff
        retry_count = _retry_tasks.get(task_name, 0)
        if retry_count < MAX_RETRIES:
            delay = BACKOFF_DELAYS[retry_count]
            _retry_tasks[task_name] = retry_count + 1
            asyncio.ensure_future(_schedule_retry(task_name, task_func, delay, **kwargs))
            logger.info(f"Scheduled retry #{retry_count + 1}/{MAX_RETRIES} for '{task_name}' in {delay}s")
        else:
            _retry_tasks.pop(task_name, None)
            logger.warning(f"Task '{task_name}' exhausted all {MAX_RETRIES} retries")

        return {"error": True, "message": str(e)[:500]}
    finally:
        _running_tasks[task_name] = False
        db.close()


async def _schedule_retry(task_name: str, task_func, delay: float, **kwargs):
    """Wait and retry the task with exponential backoff."""
    logger.info(f"Retrying task '{task_name}' in {delay}s")
    await asyncio.sleep(delay)
    await run_task(task_name, task_func, **kwargs)


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
    """Scheduled job to send weekly summary via all configured notifiers."""
    from app.services.notifier_manager import manager
    db = SessionLocal()
    try:
        manager.send_all_weekly_summaries(db)
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


def _read_schedule_settings():
    """Read schedule settings from DB."""
    db = SessionLocal()
    try:
        return {
            "schedule": get_setting(db, "check_schedule", "weekly"),
            "weekday": get_setting(db, "check_weekday", "mon"),
            "check_time": get_setting(db, "check_time", "09:00"),
            "custom_interval": get_setting(db, "custom_interval_minutes", "60"),
            "check_monthday": get_setting(db, "check_monthday", "1"),
        }
    finally:
        db.close()


def _configure_scheduler_jobs(sched: AsyncIOScheduler, cfg: dict | None = None):
    """Add or replace all scheduled jobs on a (possibly running) scheduler."""
    if cfg is None:
        cfg = _read_schedule_settings()

    schedule = cfg["schedule"]
    weekday = cfg["weekday"]
    check_time = cfg["check_time"]
    custom_interval = cfg["custom_interval"]
    check_monthday = cfg["check_monthday"]

    # Stars sync — every 6 hours
    sched.add_job(
        sync_stars_job,
        IntervalTrigger(hours=6),
        id="sync_stars",
        name="Sync GitHub Stars",
        replace_existing=True,
    )

    # Release check — based on schedule
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
    elif schedule == "monthly":
        try:
            hour, minute = check_time.split(":", 1)
            day = max(1, min(31, int(check_monthday)))
            if day > 28:
                logger.warning("Monthly check day %d — will not fire in months with fewer days", day)
            trigger = CronTrigger(day=day, hour=int(hour), minute=int(minute))
        except (ValueError, IndexError):
            trigger = CronTrigger(day=1, hour=9, minute=0)
    elif schedule == "custom":
        try:
            minutes = max(15, int(custom_interval))
            trigger = IntervalTrigger(minutes=minutes)
        except (ValueError, TypeError):
            trigger = IntervalTrigger(hours=24)
    else:
        trigger = CronTrigger(day_of_week=0, hour=9, minute=0)

    sched.add_job(
        check_releases_job,
        trigger,
        id="check_releases",
        name="Check Releases",
        replace_existing=True,
    )

    # Weekly summary — always weekly
    try:
        hour, minute = check_time.split(":", 1)
        weekday_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        day = weekday_map.get(weekday.lower(), 0)
        summary_trigger = CronTrigger(day_of_week=day, hour=int(hour), minute=int(minute))
    except (ValueError, IndexError):
        summary_trigger = CronTrigger(day_of_week=0, hour=9, minute=30)

    sched.add_job(
        weekly_summary_job,
        summary_trigger,
        id="weekly_summary",
        name="Weekly Summary Email",
        replace_existing=True,
    )

    # Cleanup — daily at 03:00
    sched.add_job(
        cleanup_logs_job,
        CronTrigger(hour=3, minute=0),
        id="cleanup_logs",
        name="Cleanup Old Logs",
        replace_existing=True,
    )


def init_scheduler():
    """Initialize and configure the APScheduler based on settings."""
    global scheduler
    if scheduler and scheduler.running:
        # Just update jobs without shutting down (avoids interrupting tasks)
        logger.info("Updating scheduler jobs")
        _configure_scheduler_jobs(scheduler)
        return

    scheduler = AsyncIOScheduler(timezone="utc")
    _configure_scheduler_jobs(scheduler)
    scheduler.start()
    logger.info("Task scheduler initialized")

    # Run initial sync on first startup only
    db = SessionLocal()
    try:
        username = get_setting(db, "github_username", "")
        token = get_setting(db, "github_token", "")
        if username and token:
            asyncio.ensure_future(sync_stars_job())
    finally:
        db.close()


def reload_scheduler():
    """Reload the scheduler (called when settings change)."""
    logger.info("Reloading scheduler due to settings change")
    init_scheduler()
