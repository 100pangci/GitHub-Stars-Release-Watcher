"""GitHub Stars Release Watcher - Main Application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.crypto import migrate_secrets_from_db
from app.database import init_db
from app.security import ensure_password_configured, ensure_session_secret
from app.services.logs import setup_logging
from app.services.notifier_manager import manager
from app.services.notifiers.email import EmailNotifier
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

    # Ensure session secret first — password encryption depends on it
    ensure_session_secret()
    ensure_password_configured()

    # Encrypt any existing plaintext secrets
    migrate_secrets_from_db()

    # Register notification channels
    manager.register(EmailNotifier)

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


# Import and register routers
from app.routers import auth, dashboard, events, health, repos, settings_route, tasks  # noqa: E402

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(repos.router)
app.include_router(events.router)
app.include_router(settings_route.router)
app.include_router(tasks.router)

# Serve SPA — serve actual files, fall back to index.html for client-side routing
SPA_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/", include_in_schema=False)
async def serve_index():
    index_path = SPA_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())
    return HTMLResponse(content="<h1>Frontend not built</h1><p>cd frontend && npm run build</p>")


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Serve SPA routes, add security headers, and protect API routes with CSRF."""
    path = request.url.path

    # --- SPA fallback (GET/HEAD only — POST and friends must reach FastAPI routes) ---
    # API routes and health check must reach FastAPI; everything else is the SPA.
    if request.method in ("GET", "HEAD") and not path.startswith("/api/") and path != "/health":
        file_path = SPA_DIR / path.lstrip("/")
        if file_path.is_file():
            return FileResponse(str(file_path))
        index_path = SPA_DIR / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text())
        return HTMLResponse(content="<h1>Frontend not built</h1><p>cd frontend && npm run build</p>")

    # --- CSRF protection for state-changing API requests ---
    # /login and /logout are exempt (no session yet / safe)
    if request.method in ("POST", "PUT", "DELETE", "PATCH") and path not in ("/login", "/logout"):
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
    csp = "; ".join([
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data:",
        "connect-src 'self'",
        "manifest-src 'self'",
    ])
    response.headers["Content-Security-Policy"] = csp
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
