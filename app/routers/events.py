"""Events/Updates router."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.models import Event, Repo
from app.security import validate_session

router = APIRouter()


@router.get("/api/events")
async def events_api(
    request: Request,
    repo_id: str = "",
):
    """Events/Updates API."""
    if not validate_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        query = db.query(Event)

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

        return JSONResponse(event_list)
    finally:
        db.close()
