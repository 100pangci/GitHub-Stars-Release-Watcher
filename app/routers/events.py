"""Events/Updates router."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models import Event, Repo
from app.security import validate_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/events", response_class=HTMLResponse)
async def events_page(
    request: Request,
    source: str = "all",
    repo_id: str = "",
):
    """Events/Updates page."""
    if not validate_session(request):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    try:
        query = db.query(Event)

        if source == "release":
            query = query.join(Event.version).filter(Event.version.has(source="release"))
        elif source == "tag":
            query = query.join(Event.version).filter(Event.version.has(source="tag"))

        if repo_id and repo_id.isdigit():
            query = query.filter(Event.repo_id == int(repo_id))

        events = query.order_by(Event.created_at.desc()).limit(200).all()

        event_list = []
        for evt in events:
            repo = db.query(Repo).filter(Repo.id == evt.repo_id).first()
            event_list.append({
                "id": evt.id,
                "title": evt.title,
                "message": evt.message,
                "event_type": evt.event_type,
                "created_at": evt.created_at,
                "repo_name": repo.full_name if repo else "Unknown",
                "repo_url": repo.html_url if repo else "#",
            })

        # Get all repos for filter dropdown
        repos = db.query(Repo).order_by(Repo.full_name).all()

        return templates.TemplateResponse(
            "events.html",
            {
                "request": request,
                "events": event_list,
                "source": source,
                "repo_id": repo_id,
                "repos": repos,
            },
        )
    finally:
        db.close()