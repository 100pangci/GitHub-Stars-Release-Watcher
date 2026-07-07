"""Settings router - note: named settings_route.py to avoid conflict with settings service."""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.security import validate_session
from app.services.emailer import is_email_configured, send_test_email
from app.services.scheduler import reload_scheduler
from app.services.settings import get_setting, is_secret_set, set_setting, validate_github_username, validate_port

router = APIRouter()


@router.get("/api/settings")
async def settings_api(request: Request):
    """Get all settings as JSON."""
    if not validate_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        settings_data = {
            "github_username": get_setting(db, "github_username", ""),
            "github_token_set": is_secret_set(db, "github_token"),
            "check_schedule": get_setting(db, "check_schedule", "weekly"),
            "check_weekday": get_setting(db, "check_weekday", "mon"),
            "check_time": get_setting(db, "check_time", "09:00"),
            "custom_interval_minutes": get_setting(db, "custom_interval_minutes", "60"),
            "monitor_prereleases": get_setting(db, "monitor_prereleases", "false"),
            "fallback_to_tags": get_setting(db, "fallback_to_tags", "true"),
            "ignore_archived": get_setting(db, "ignore_archived", "true"),
            "allow_initial_notifications": get_setting(db, "allow_initial_notifications", "false"),
            "github_request_delay": get_setting(db, "github_request_delay", "0.2"),
            "send_no_updates_email": get_setting(db, "send_no_updates_email", "true"),
            "smtp_host": get_setting(db, "smtp_host", ""),
            "smtp_port": get_setting(db, "smtp_port", "587"),
            "smtp_username": get_setting(db, "smtp_username", ""),
            "smtp_password_set": is_secret_set(db, "smtp_password"),
            "smtp_use_tls": get_setting(db, "smtp_use_tls", "true"),
            "smtp_from_addr": get_setting(db, "smtp_from_addr", ""),
            "smtp_to_addr": get_setting(db, "smtp_to_addr", ""),
            "email_configured": is_email_configured(db),
        }
        return JSONResponse(settings_data)
    finally:
        db.close()


@router.post("/api/settings/github")
async def save_github_settings(
    request: Request,
    github_username: str = Form(""),
    github_token: str = Form(""),
):
    """Save GitHub settings."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    errors = []
    if github_username and not validate_github_username(github_username):
        errors.append("Invalid GitHub username format")

    if errors:
        return JSONResponse({"success": False, "message": "; ".join(errors)}, status_code=400)

    db = SessionLocal()
    try:
        set_setting(db, "github_username", github_username)
        if github_token:
            set_setting(db, "github_token", github_token, secret=True)
        db.commit()
        return JSONResponse({"success": True, "message": "GitHub settings saved"})
    except Exception as e:
        db.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/settings/schedule")
async def save_schedule_settings(
    request: Request,
    check_schedule: str = Form("weekly"),
    check_weekday: str = Form("mon"),
    check_time: str = Form("09:00"),
    custom_interval_minutes: str = Form("60"),
):
    """Save schedule settings."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    valid_schedules = ["hourly", "daily", "weekly", "custom"]
    if check_schedule not in valid_schedules:
        return JSONResponse({"success": False, "message": "Invalid schedule"}, status_code=400)

    if check_schedule == "custom":
        try:
            minutes = int(custom_interval_minutes)
            if minutes < 15:
                return JSONResponse(
                    {"success": False, "message": "Custom interval must be at least 15 minutes"},
                    status_code=400,
                )
        except ValueError:
            return JSONResponse({"success": False, "message": "Invalid interval"}, status_code=400)

    valid_weekdays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    if check_weekday.lower() not in valid_weekdays:
        return JSONResponse({"success": False, "message": "Invalid weekday"}, status_code=400)

    db = SessionLocal()
    try:
        set_setting(db, "check_schedule", check_schedule)
        set_setting(db, "check_weekday", check_weekday.lower())
        set_setting(db, "check_time", check_time)
        set_setting(db, "custom_interval_minutes", custom_interval_minutes)
        db.commit()
        reload_scheduler()
        return JSONResponse({"success": True, "message": "Schedule settings saved"})
    except Exception as e:
        db.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/settings/release-policy")
async def save_release_policy(
    request: Request,
    monitor_prereleases: str = Form("false"),
    fallback_to_tags: str = Form("true"),
    ignore_archived: str = Form("true"),
    allow_initial_notifications: str = Form("false"),
    send_no_updates_email: str = Form("true"),
    github_request_delay: str = Form("0.2"),
):
    """Save release/tag policy settings."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        delay = float(github_request_delay)
        if delay < 0.01:
            return JSONResponse({"success": False, "message": "Delay must be at least 0.01s"}, status_code=400)
    except ValueError:
        return JSONResponse({"success": False, "message": "Invalid delay value"}, status_code=400)

    db = SessionLocal()
    try:
        set_setting(db, "monitor_prereleases", monitor_prereleases)
        set_setting(db, "fallback_to_tags", fallback_to_tags)
        set_setting(db, "ignore_archived", ignore_archived)
        set_setting(db, "allow_initial_notifications", allow_initial_notifications)
        set_setting(db, "send_no_updates_email", send_no_updates_email)
        set_setting(db, "github_request_delay", github_request_delay)
        db.commit()
        return JSONResponse({"success": True, "message": "Release/Tag policy saved"})
    except Exception as e:
        db.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/settings/email")
async def save_email_settings(
    request: Request,
    smtp_host: str = Form(""),
    smtp_port: str = Form("587"),
    smtp_username: str = Form(""),
    smtp_password: str = Form(""),
    smtp_use_tls: str = Form("true"),
    smtp_from_addr: str = Form(""),
    smtp_to_addr: str = Form(""),
):
    """Save SMTP/email settings."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not validate_port(smtp_port):
        return JSONResponse({"success": False, "message": "SMTP port must be between 1 and 65535"}, status_code=400)

    db = SessionLocal()
    try:
        set_setting(db, "smtp_host", smtp_host)
        set_setting(db, "smtp_port", smtp_port)
        set_setting(db, "smtp_username", smtp_username)
        if smtp_password:
            set_setting(db, "smtp_password", smtp_password, secret=True)
        set_setting(db, "smtp_use_tls", smtp_use_tls)
        set_setting(db, "smtp_from_addr", smtp_from_addr)
        set_setting(db, "smtp_to_addr", smtp_to_addr)
        db.commit()
        return JSONResponse({"success": True, "message": "Email settings saved"})
    except Exception as e:
        db.rollback()
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/api/settings/test-email")
async def test_email(request: Request):
    """Send a test email."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

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
