"""Task trigger router - handles manual task execution via POST."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.models import Repo, Setting
from app.security import validate_session
from app.services.settings import get_setting
from app.services.scheduler import run_task, sync_stars_job, check_releases_job, weekly_summary_job
from app.services.emailer import send_test_email, is_email_configured

router = APIRouter()


@router.post("/api/tasks/sync-stars")
async def trigger_sync_stars(request: Request):
    """Manually trigger stars sync."""
    if not validate_session(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        username = get_setting(db, "github_username", "")
        token = get_setting(db, "github_token", "")
        delay = float(get_setting(db, "github_request_delay", "0.2"))

        if not username or not token:
            return JSONResponse({"success": False, "message": "GitHub username or token not configured"}, status_code=400)

        from app.services.stars import sync_stars as _sync_stars
        result = await run_task("sync_stars", _sync_stars, username=username, token=token, delay=delay)
        return JSONResponse({
            "success": True,
            "message": result.get("message", "Stars synced"),
            "data": result,
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/tasks/check-releases")
async def trigger_check_releases(request: Request):
    """Manually trigger release check."""
    if not validate_session(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        token = get_setting(db, "github_token", "")
        delay = float(get_setting(db, "github_request_delay", "0.2"))

        if not token:
            return JSONResponse({"success": False, "message": "GitHub token not configured"}, status_code=400)

        from app.services.releases import check_releases as _check_releases
        result = await run_task("check_releases", _check_releases, token=token, delay=delay)
        return JSONResponse({
            "success": True,
            "message": result.get("message", "Release check completed"),
            "data": result,
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/tasks/weekly-summary")
async def trigger_weekly_summary(request: Request):
    """Manually trigger weekly summary."""
    if not validate_session(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        if not is_email_configured(db):
            return JSONResponse({"success": False, "message": "Email not configured"}, status_code=400)

        from app.services.emailer import send_weekly_summary
        result = send_weekly_summary(db)
        return JSONResponse({
            "success": result["sent"],
            "message": result.get("message", "Summary sent"),
            "data": result,
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/tasks/send-test-email")
async def trigger_test_email(request: Request):
    """Send test email."""
    if not validate_session(request):
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        result = send_test_email(db)
        return JSONResponse({"success": True, "message": result})
    except ValueError as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Email sending failed: {e}"}, status_code=500)
    finally:
        db.close()