"""Authentication router - login, logout, change password."""

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.security import (
    verify_password,
    get_stored_password_hash,
    set_stored_password_hash,
    hash_password,
    create_session,
    destroy_session,
    validate_session,
    is_password_configured,
    ensure_password_configured,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    if validate_session(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    password: str = Form(...),
):
    """Process login."""
    stored_hash = get_stored_password_hash()
    if not stored_hash or not verify_password(password, stored_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid password"},
        )

    response = RedirectResponse(url="/", status_code=303)
    create_session(response)
    return response


@router.post("/logout")
async def logout():
    """Logout and destroy session."""
    response = RedirectResponse(url="/login", status_code=303)
    destroy_session(response)
    return response


@router.post("/api/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
):
    """Change the web login password."""
    if not validate_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    stored_hash = get_stored_password_hash()
    if not stored_hash or not verify_password(current_password, stored_hash):
        return JSONResponse(
            {"success": False, "message": "Current password is incorrect"},
            status_code=400,
        )

    if len(new_password) < 4:
        return JSONResponse(
            {"success": False, "message": "New password must be at least 4 characters"},
            status_code=400,
        )

    set_stored_password_hash(hash_password(new_password))

    return JSONResponse({"success": True, "message": "Password changed successfully"})