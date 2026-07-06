"""Settings management routes."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
import re

from app.security import check_auth_sync
from app.services.settings import (
    get_setting, set_setting, delete_setting,
    get_all_settings, is_github_configured, is_smtp_configured,
    verify_app_password, set_app_password,
)
from app.services.scheduler import reload_schedule, get_schedule_config
from app.config import settings as app_settings

router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


class GitHubSettings(BaseModel):
    username: str = Field("", max_length=100)
    token: str = Field("")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if v and not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]*$", v):
            raise ValueError("Invalid GitHub username format")
        return v


class ScheduleSettings(BaseModel):
    schedule: str = "weekly"
    weekday: str = "mon"
    check_time: str = "09:00"

    @field_validator("check_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        if v and not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Time must be in HH:MM format (24h)")
        return v


class ReleaseSettings(BaseModel):
    monitor_prereleases: str = "false"
    fallback_to_tags: str = "true"
    ignore_archived: str = "true"
    allow_initial_notifications: str = "false"
    send_no_updates_email: str = "false"


class SMTPSettings(BaseModel):
    host: str = ""
    port: int = Field(default=587, ge=1, le=65535)
    username: str = ""
    password: str = ""
    use_tls: str = "true"
    from_addr: str = ""
    to_addr: str = ""


class PasswordSettings(BaseModel):
    current_password: str = ""
    new_password: str = Field("", min_length=6, max_length=255)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    if not check_auth_sync(request):
        return RedirectResponse(url="/login", status_code=302)

    all_settings = get_all_settings()

    github = {
        "username": get_setting("github_username") or app_settings.github_username or "",
        "token_set": bool(get_setting("github_token") or app_settings.github_token),
    }

    schedule_config = get_schedule_config()

    release_cfg = {
        "monitor_prereleases": get_setting("monitor_prereleases") or "false",
        "fallback_to_tags": get_setting("fallback_to_tags") or "true",
        "ignore_archived": get_setting("ignore_archived") or "true",
        "allow_initial_notifications": get_setting("allow_initial_notifications") or "false",
        "send_no_updates_email": get_setting("send_no_updates_email") or "false",
    }

    smtp = {
        "host": get_setting("smtp_host") or "",
        "port": get_setting("smtp_port") or "587",
        "username": get_setting("smtp_username") or "",
        "password_set": bool(get_setting("smtp_password")),
        "use_tls": get_setting("smtp_use_tls") or "true",
        "from_addr": get_setting("smtp_from_addr") or "",
        "to_addr": get_setting("smtp_to_addr") or "",
    }

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "github": github,
        "schedule": schedule_config,
        "release": release_cfg,
        "smtp": smtp,
    })


@router.post("/settings/github")
async def save_github_settings(
    request: Request,
    github_username: str = Form(""),
    github_token: str = Form(""),
):
    if not check_auth_sync(request):
        return RedirectResponse(url="/login", status_code=302)

    try:
        validated = GitHubSettings(username=github_username, token="")
        set_setting("github_username", validated.username)

        if github_token:
            set_setting("github_token", github_token, secret=True)

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "github": {
                    "username": validated.username,
                    "token_set": bool(get_setting("github_token") or app_settings.github_token),
                },
                "schedule": get_schedule_config(),
                "release": {
                    "monitor_prereleases": get_setting("monitor_prereleases") or "false",
                    "fallback_to_tags": get_setting("fallback_to_tags") or "true",
                    "ignore_archived": get_setting("ignore_archived") or "true",
                    "allow_initial_notifications": get_setting("allow_initial_notifications") or "false",
                    "send_no_updates_email": get_setting("send_no_updates_email") or "false",
                },
                "smtp": {
                    "host": get_setting("smtp_host") or "",
                    "port": get_setting("smtp_port") or "587",
                    "username": get_setting("smtp_username") or "",
                    "password_set": bool(get_setting("smtp_password")),
                    "use_tls": get_setting("smtp_use_tls") or "true",
                    "from_addr": get_setting("smtp_from_addr") or "",
                    "to_addr": get_setting("smtp_to_addr") or "",
                },
                "flash": {"type": "success", "message": "GitHub settings saved successfully"},
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "github": {"username": github_username, "token_set": bool(get_setting("github_token") or app_settings.github_token)},
                "schedule": get_schedule_config(),
                "release": {
                    "monitor_prereleases": get_setting("monitor_prereleases") or "false",
                    "fallback_to_tags": get_setting("fallback_to_tags") or "true",
                    "ignore_archived": get_setting("ignore_archived") or "true",
                    "allow_initial_notifications": get_setting("allow_initial_notifications") or "false",
                    "send_no_updates_email": get_setting("send_no_updates_email") or "false",
                },
                "smtp": {
                    "host": get_setting("smtp_host") or "",
                    "port": get_setting("smtp_port") or "587",
                    "username": get_setting("smtp_username") or "",
                    "password_set": bool(get_setting("smtp_password")),
                    "use_tls": get_setting("smtp_use_tls") or "true",
                    "from_addr": get_setting("smtp_from_addr") or "",
                    "to_addr": get_setting("smtp_to_addr") or "",
                },
                "flash": {"type": "error", "message": str(e)},
            },
            status_code=400,
        )


@router.post("/settings/schedule")
async def save_schedule_settings(
    request: Request,
    check_schedule: str = Form("weekly"),
    check_weekday: str = Form("mon"),
    check_time: str = Form("09:00"),
):
    if not check_auth_sync(request):
        return RedirectResponse(url="/login", status_code=302)

    try:
        validated = ScheduleSettings(
            schedule=check_schedule,
            weekday=check_weekday,
            check_time=check_time,
        )

        # Minimum interval check for custom schedules
        set_setting("check_schedule", validated.schedule)
        set_setting("check_weekday", validated.weekday)
        set_setting("check_time", validated.check_time)

        # Reload scheduler
        reload_schedule()

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "github": {
                    "username": get_setting("github_username") or app_settings.github_username or "",
                    "token_set": bool(get_setting("github_token") or app_settings.github_token),
                },
                "schedule": get_schedule_config(),
                "release": {
                    "monitor_prereleases": get_setting("monitor_prereleases") or "false",
                    "fallback_to_tags": get_setting("fallback_to_tags") or "true",
                    "ignore_archived": get_setting("ignore_archived") or "true",
                    "allow_initial_notifications": get_setting("allow_initial_notifications") or "false",
                    "send_no_updates_email": get_setting("send_no_updates_email") or "false",
                },
                "smtp": {
                    "host": get_setting("smtp_host") or "",
                    "port": get_setting("smtp_port") or "587",
                    "username": get_setting("smtp_username") or "",
                    "password_set": bool(get_setting("smtp_password")),
                    "use_tls": get_setting("smtp_use_tls") or "true",
                    "from_addr": get_setting("smtp_from_addr") or "",
                    "to_addr": get_setting("smtp_to_addr") or "",
                },
                "flash": {"type": "success", "message": "Schedule settings saved successfully"},
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "schedule": {"schedule": check_schedule, "weekday": check_weekday, "time": check_time},
                "flash": {"type": "error", "message": str(e)},
            },
            status_code=400,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "error", "message": f"Failed to update schedule: {str(e)[:200]}"},
            },
            status_code=400,
        )


@router.post("/settings/release")
async def save_release_settings(
    request: Request,
    monitor_prereleases: str = Form("false"),
    fallback_to_tags: str = Form("true"),
    ignore_archived: str = Form("true"),
    allow_initial_notifications: str = Form("false"),
    send_no_updates_email: str = Form("false"),
):
    if not check_auth_sync(request):
        return RedirectResponse(url="/login", status_code=302)

    try:
        validated = ReleaseSettings(
            monitor_prereleases=monitor_prereleases,
            fallback_to_tags=fallback_to_tags,
            ignore_archived=ignore_archived,
            allow_initial_notifications=allow_initial_notifications,
            send_no_updates_email=send_no_updates_email,
        )

        set_setting("monitor_prereleases", validated.monitor_prereleases)
        set_setting("fallback_to_tags", validated.fallback_to_tags)
        set_setting("ignore_archived", validated.ignore_archived)
        set_setting("allow_initial_notifications", validated.allow_initial_notifications)
        set_setting("send_no_updates_email", validated.send_no_updates_email)

        # Reload schedule to apply any changes
        reload_schedule()

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "success", "message": "Release settings saved successfully"},
            },
            status_code=200,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "error", "message": str(e)},
            },
            status_code=400,
        )


@router.post("/settings/smtp")
async def save_smtp_settings(
    request: Request,
    smtp_host: str = Form(""),
    smtp_port: int = Form(587),
    smtp_username: str = Form(""),
    smtp_password: str = Form(""),
    smtp_use_tls: str = Form("true"),
    smtp_from_addr: str = Form(""),
    smtp_to_addr: str = Form(""),
):
    if not check_auth_sync(request):
        return RedirectResponse(url="/login", status_code=302)

    try:
        validated = SMTPSettings(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=smtp_use_tls,
            from_addr=smtp_from_addr,
            to_addr=smtp_to_addr,
        )

        set_setting("smtp_host", validated.host)
        set_setting("smtp_port", str(validated.port))
        set_setting("smtp_username", validated.username)
        if validated.password:
            set_setting("smtp_password", validated.password, secret=True)
        set_setting("smtp_use_tls", validated.use_tls)
        set_setting("smtp_from_addr", validated.from_addr)
        set_setting("smtp_to_addr", validated.to_addr)

        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "success", "message": "SMTP settings saved successfully"},
            },
            status_code=200,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "error", "message": str(e)},
            },
            status_code=400,
        )


@router.post("/settings/password")
async def change_password(
    request: Request,
    current_password: str = Form(""),
    new_password: str = Form(""),
):
    if not check_auth_sync(request):
        return RedirectResponse(url="/login", status_code=302)

    if not current_password or not new_password:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "error", "message": "Both current and new password are required"},
            },
            status_code=400,
        )

    if not verify_app_password(current_password):
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "error", "message": "Current password is incorrect"},
            },
            status_code=400,
        )

    try:
        set_app_password(new_password)
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "success", "message": "Password changed successfully"},
            },
            status_code=200,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "flash": {"type": "error", "message": str(e)},
            },
            status_code=400,
        )