"""GitHub Stars Release Watcher - Main Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db
from app.security import ensure_password_configured
from app.services.scheduler import init_scheduler
from app.services.logs import setup_logging, add_log

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting GitHub Stars Release Watcher...")

    # Initialize database
    init_db()

    # Ensure password is configured (generate if needed)
    ensure_password_configured()

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

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Import and register routers
from app.routers import health, auth, dashboard, repos, events, settings_route, tasks

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(repos.router)
app.include_router(events.router)
app.include_router(settings_route.router)
app.include_router(tasks.router)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


templates = Jinja2Templates(directory="app/templates")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )