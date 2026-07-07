"""Repositories router."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.models import Repo, RepoState
from app.security import validate_session

router = APIRouter()


@router.get("/api/repos")
async def repos_api(request: Request, search: str = "", filter: str = "all"):
    """Repos list API."""
    if not validate_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    db = SessionLocal()
    try:
        query = db.query(Repo)
        if search:
            query = query.filter(Repo.full_name.ilike(f"%{search}%"))
        if filter == "active":
            query = query.filter(Repo.active == True)  # noqa: E712
        elif filter == "inactive":
            query = query.filter(Repo.active == False)  # noqa: E712
        elif filter == "archived":
            query = query.filter(Repo.archived == True)  # noqa: E712
        elif filter == "has_updates":
            query = query.filter(Repo.repo_state.has(RepoState.current_version.isnot(None)))

        repos = query.order_by(Repo.full_name).all()
        result = []
        for repo in repos:
            state = repo.repo_state
            result.append({
                "id": repo.id,
                "full_name": repo.full_name,
                "html_url": repo.html_url,
                "description": repo.description or "",
                "language": repo.language or "",
                "archived": repo.archived,
                "active": repo.active,
                "pushed_at": repo.pushed_at,
                "last_synced_at": repo.last_synced_at,
                "last_checked_at": repo.last_checked_at,
                "current_version": state.current_version if state else None,
                "current_source": state.current_source if state else None,
                "current_version_url": state.current_version_url if state else None,
            })
        return JSONResponse(result)
    finally:
        db.close()
