"""Dashboard router."""

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models import Repo, Event, TaskRun, Setting
from app.security import validate_session
from app.services.settings import get_setting

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_dashboard_stats():
    """Get dashboard statistics."""
    db = SessionLocal()
    try:
        total_stars = db.query(Repo).count()
        active_repos = db.query(Repo).filter(Repo.active == True).count()  # noqa: E712
        inactive_repos = db.query(Repo).filter(Repo.active == False).count()  # noqa: E712

        # Get this week's events
        week_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7) if week_ago.day > 7 else week_ago
        from datetime import timedelta
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
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


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page."""
    if not validate_session(request):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=303)

    stats = get_dashboard_stats()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats},
    )


@router.get("/api/dashboard/stats")
async def dashboard_stats_api(request: Request):
    """Dashboard stats API."""
    if not validate_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    stats = get_dashboard_stats()
    return JSONResponse(stats)