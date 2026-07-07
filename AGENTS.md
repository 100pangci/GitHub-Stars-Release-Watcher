# GitHub Stars Release Watcher – Agent Guide

## Quick start
```bash
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pytest
cd frontend && npm install && npm run dev  # SPA dev server
```

## Architecture

- **FastAPI app** at `app/main.py` – lifespan inits DB, passwords, and scheduler
- **Config**: `app/config.py` – pydantic-settings, env vars with no prefix (e.g. `APP_PASSWORD`, `DATABASE_URL`)
- **DB**: SQLite via SQLAlchemy, WAL mode + foreign keys enforced via `@event.listens_for`
- **Auth**: session cookie (`gsrw_session`) via itsdangerous URLSafeTimedSerializer, bcrypt password hash
- **Scheduler**: APScheduler AsyncIOScheduler with 4 jobs (sync_stars 6h, check_releases configurable, weekly_summary same time, cleanup_logs daily 03:00)
- **GitHub client**: httpx AsyncClient, 30s timeout, 0.2s delay between requests, rate-limit tracking from response headers
- **Settings**: key-value store in `settings` DB table, secret values encrypted at rest via `cryptography.fernet.Fernet` (key derived from `SESSION_SECRET` via PBKDF2). `app/crypto.py` handles encrypt/decrypt transparently in `set_setting`/`get_setting`.
- **Security**: CSRF via Origin/Referer check on all POST requests (`app/main.py:security_middleware`); login rate-limited to 5 attempts per 15 min per IP; password min 8 chars.
- **Frontend**: Vue 3 + TypeScript SPA in `frontend/`, built to `frontend/dist/`, served by FastAPI via `StaticFiles(html=True)`.

## Tests

```bash
pytest                              # all tests
pytest tests/test_github_client.py  # single file
```

- `asyncio_mode = "auto"` – no need for `@pytest.mark.asyncio` on async tests (but some tests have it anyway)
- No fixtures or external services needed – uses `unittest.mock` / `respx`
- Test paths: `tests/`

## API endpoints

All API routes are under `/api/`. The SPA communicates exclusively via JSON fetch calls.
See `app/routers/` for individual endpoints.

## Container

- `Containerfile` (Podman/Docker) – multi-stage build: Node.js builds frontend, Python slim runs app
- `compose.yaml` (Docker Compose)
- Healthcheck on `GET /health`
- Non-root `app` user, port 8000, data persisted at `/data`
- First run generates a random password printed to stdout/logs

## Things to watch

- **Env vs DB settings**: GitHub username/token, schedule, SMTP settings are stored in the DB `settings` table (set via Web UI). Env vars are initial/override values only.
- **First-run password**: Auto-generated; printed to stdout (container logs) — only during first start.
- **Session secret**: Auto-generated + persisted to DB on first start via `ensure_session_secret()` in `security.py`; survives restarts. Override with `SESSION_SECRET` env var.
- **Encryption key**: Derived from `SESSION_SECRET`; existing encrypted secrets become unreadable if `SESSION_SECRET` changes.
- **DB session management**: Functions accept optional `db` param; if `None` they create their own session. Callers must commit/close properly.
