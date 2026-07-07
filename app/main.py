"""GitHub Stars Release Watcher - Main Application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.crypto import migrate_secrets_from_db
from app.database import init_db
from app.security import ensure_password_configured, ensure_session_secret
from app.services.logs import setup_logging
from app.services.scheduler import init_scheduler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting GitHub Stars Release Watcher...")

    # Initialize database
    init_db()

    # Ensure password and session secret are configured
    ensure_password_configured()
    ensure_session_secret()

    # Encrypt any existing plaintext secrets
    migrate_secrets_from_db()

    # Initialize scheduler
    init_scheduler()

    logger.info("Application started successfully")
    yield

    # Shutdown
    logger.info("Shutting down...")
    from app.services.scheduler import scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("Shutdown complete")


app = FastAPI(
    title="GitHub Stars Release Watcher",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount SPA static files
SPA_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if SPA_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(SPA_DIR), html=True), name="spa")
else:
    # Fallback: serve index.html via catch-all route for development
    @app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        spa_index = SPA_DIR / "index.html"
        if spa_index.exists():
            return HTMLResponse(content=spa_index.read_text())
        return HTMLResponse(content="<h1>Frontend not built</h1><p>Run: cd frontend && npm run build</p>")

# Import and register routers
from app.routers import auth, dashboard, events, health, repos, settings_route, tasks  # noqa: E402

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(repos.router)
app.include_router(events.router)
app.include_router(settings_route.router)
app.include_router(tasks.router)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Add security headers and CSRF protection."""
    # CSRF protection for state-changing requests
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        host = request.headers.get("Host")
        if not host:
            return JSONResponse({"detail": "Missing Host header"}, status_code=400)
        if origin:
            parsed = urlparse(origin)
            if host != parsed.netloc:
                return JSONResponse({"detail": "CSRF: Origin mismatch"}, status_code=403)
        elif referer:
            ref_host = urlparse(referer).hostname
            if ref_host != host:
                return JSONResponse({"detail": "CSRF: Referer mismatch"}, status_code=403)
        else:
            return JSONResponse({"detail": "CSRF: Missing Origin or Referer"}, status_code=403)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
