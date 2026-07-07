"""Dashboard router."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.models import Event, Repo, TaskRun
from app.security import validate_session
from app.services.settings import get_setting

router = APIRouter()


def get_dashboard_stats():
    """Get dashboard statistics."""
    db = SessionLocal()
    try:
        total_stars = db.query(Repo).count()
        active_repos = db.query(Repo).filter(Repo.active == True).count()  # noqa: E712
        inactive_repos = db.query(Repo).filter(Repo.active == False).count()  # noqa: E712

        # Get this week's events
        week_ago = datetime.now(UTC) - timedelta(days=7)
        week_updates = db.query(Event).filter(Event.created_at >= week_ago).count()

        # Last check time
        last_run = (
            db.query(TaskRun)
            .filter(TaskRun.task_name == "check_releases")
            .order_by(TaskRun.started_at.desc())
            .first()
        )
        last_check = last_run.started_at if last_run else None
        next_check = None
        if last_run and last_run.status == "running":
            next_check = "Running..."

        # Check if configured
        github_username = get_setting(db, "github_username", "")
        github_token_set = bool(get_setting(db, "github_token", ""))

        return {
            "total_stars": total_stars,
            "active_repos": active_repos,
            "inactive_repos": inactive_repos,
            "week_updates": week_updates,
            "last_check": last_check,
            "next_check": next_check,
            "github_configured": bool(github_username and github_token_set),
        }
    finally:
        db.close()


@router.get("/api/dashboard/stats")
async def dashboard_stats_api(request: Request):
    """Dashboard stats API."""
    if not validate_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    stats = get_dashboard_stats()
    return JSONResponse(stats)


@router.get("/api/dashboard/history")
async def dashboard_history_api(request: Request):
    """Return recent task run history for charts."""
    if not validate_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        runs = (
            db.query(TaskRun)
            .filter(
                TaskRun.task_name.in_(["sync_stars", "check_releases"]),
                TaskRun.finished_at.isnot(None),
                TaskRun.started_at >= datetime.now(UTC) - timedelta(days=60),
            )
            .order_by(TaskRun.started_at.asc())
            .all()
        )
        return JSONResponse([
            {
                "id": r.id,
                "task_name": r.task_name,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "checked_repos": r.checked_repos,
                "found_updates": r.found_updates,
            }
            for r in runs
        ])
    finally:
        db.close()
