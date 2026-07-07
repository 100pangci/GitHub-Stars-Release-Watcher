# GitHub Stars Release Watcher

[中文文档](./README.zh.md)

A self-hosted application to monitor your GitHub starred repositories for new releases and tags. Get weekly summaries of all new versions from your starred projects via email (or any future notification channel).

## Features

- **GitHub Stars Sync** – Automatically sync your starred repositories
- **Release/Tag Monitoring** – Check each repo for new GitHub Releases and tags (supports prereleases, tag fallback)
- **Weekly Summary** – Receive a comprehensive weekly report with all new updates
- **Notification Framework** – Extensible notifier system (SMTP email built-in; add webhook, Telegram, etc. easily)
- **Flexible Scheduling** – Hourly, daily, weekly, monthly, or custom interval
- **Web UI** – Easy-to-use interface for configuration and monitoring (Vue 3 + Vuetify 3, MD3 design)
- **No External Dependencies** – SQLite database, no Redis/Postgres/Celery needed
- **Single Container** – Everything runs in one Podman/Docker container
- **Multi-language UI** – English, Chinese, Japanese

## Quick Start

### Using Podman

```bash
# Build the image
podman build -t github-stars-release-watcher:latest .

# Create data directory
mkdir -p data

# Run the container
podman run -d --name github-stars-release-watcher \
  -p 8000:8000 \
  -v ./data:/data:z \
  -e APP_PASSWORD='your-secure-password' \
  --restart=always \
  github-stars-release-watcher:latest
```

Then open http://localhost:8000 and log in with your password.

> **Note**: `SESSION_SECRET` is auto-generated and persisted to the database on first start — you don't need to set it unless you want to override.

### Using Docker

```bash
# Build the image
docker build -t github-stars-release-watcher:latest -f Containerfile .

# Run the container
docker run -d --name github-stars-release-watcher \
  -p 8000:8000 \
  -v ./data:/data \
  -e APP_PASSWORD='your-secure-password' \
  --restart=always \
  github-stars-release-watcher:latest
```

### Using Docker Compose

```bash
# Start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down

# Rebuild and start after updating
docker compose up -d --build
```

The project includes a `compose.yaml` with sensible defaults. You can also use a `.env` file alongside `compose.yaml`:

```bash
# .env
APP_PASSWORD=your-secure-password
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_PASSWORD` | No* | Auto-generated | Password for Web UI login |
| `SESSION_SECRET` | No* | Auto-generated | Secret key for session cookies and encryption |
| `APP_COOKIE_SECURE` | No | `false` | Set to `true` if using HTTPS behind a reverse proxy |
| `DATABASE_URL` | No | `sqlite:////data/app.db` | Database path |
| `GITHUB_USERNAME` | No | – | GitHub username (can be set in Web UI) |
| `GITHUB_TOKEN` | No | – | GitHub Personal Access Token (can be set in Web UI) |
| `CHECK_SCHEDULE` | No | `weekly` | Check frequency: `hourly`, `daily`, `weekly`, `monthly`, `custom` |
| `CHECK_WEEKDAY` | No | `mon` | Day for weekly checks |
| `CHECK_TIME` | No | `09:00` | Time for scheduled checks (UTC) |
| `MONITOR_PRERELEASES` | No | `false` | Include prerelease versions |
| `DATA_DIR` | No | `/data` | Data directory for database and logs |

*\* If `APP_PASSWORD` is not set, a random password is generated on first start and printed to the container log. `SESSION_SECRET` is auto-generated on first start and persisted in the database.*

## Setup

### 1. GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Create a new token with at least `repo` scope (for private repos) or no scope (for public repos only)
3. Copy the token and enter it in the Web UI Settings page

### 2. Configure the Application

After logging in to the Web UI:

1. **GitHub Settings**: Enter your GitHub username and Personal Access Token
2. **Schedule Settings**: Configure how often to check for releases (hourly/daily/weekly/monthly/custom)
3. **Release/Tag Strategy**: Configure monitoring preferences (prereleases, tag fallback, archived repos)
4. **Notification Settings**: Configure email (SMTP) for weekly summaries

### 3. Initial Sync

1. Go to Dashboard and click **Sync Stars Now** to fetch your starred repositories
2. Then click **Check Releases Now** to scan for releases

The first check will initialize the state of all repos (it will not send notifications unless `allow_initial_notifications` is enabled in settings).

## Podman Systemd Integration

```bash
# Generate a systemd unit file
podman generate systemd --new --name github-stars-release-watcher > ~/.config/systemd/user/github-stars-release-watcher.service

# Enable and start
systemctl --user enable --now github-stars-release-watcher.service
```

See [the source README](./README.md) for a root-level systemd unit example.

## Web UI Pages

- **Dashboard** – Overview with stats, rate limit status, system health, and task history
- **Repositories** – Browse and search your starred repos, check individual repos
- **Events / Updates** – View detected release/tag events
- **Settings** – Configure GitHub, schedule, release strategy, notifications
- **Logs** – View recent application logs

## Adding a New Notification Channel

The notification framework (`app/services/notifiers/`) makes it easy to add custom channels:

1. Create `app/services/notifiers/my_channel.py` with a class inheriting `BaseNotifier`
2. Implement `name`, `display_name`, `is_configured`, `get_settings`, `save_settings`
3. Register in `app/main.py:lifespan` via `manager.register(MyNotifier)`
4. The settings API and scheduler automatically pick up the new notifier

## Security Notes

- GitHub token and SMTP password are encrypted at rest using Fernet (symmetric encryption)
- Secrets are never displayed in the Web UI or logs
- Session cookies use HttpOnly, SameSite=Lax attributes
- All configuration changes require authentication
- CSRF protection on all POST/PUT/DELETE/PATCH requests (Origin/Referer check)
- Login rate-limited to 5 attempts per 15 minutes per IP
- Password minimum 8 characters
- Content-Security-Policy header set on all responses

## Development

### Prerequisites

- Python 3.12+
- Node.js 20+ (for frontend development)
- pip

### Setup

```bash
# Clone the repository
cd github-stars-release-watcher

# Install Python dependencies
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install && cd ..

# Quick start (backend + frontend dev servers in separate windows)
dev.bat          # Windows
# or
./dev.ps1        # PowerShell
```

Alternatively, start manually:

```bash
# Terminal 1: Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (Vite dev server on port 5173)
cd frontend && npm run dev
```

### Running Tests

```bash
pytest                              # all tests
pytest tests/test_github_client.py  # single file
```

Test files cover:
- `test_crypto.py` – Encryption/decryption roundtrip and edge cases
- `test_github_client.py` – GitHub API client initialization, headers, rate limiting
- `test_release_detection.py` – Release/tag parsing from GitHub API responses
- `test_settings_encryption.py` – Secret settings at-rest encryption
- `test_settings_validation.py` – SMTP port and GitHub username validation

## Project Structure

```
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment configuration (pydantic-settings)
│   ├── crypto.py                # Fernet encryption/decryption for secrets at rest
│   ├── database.py              # Database engine & session (SQLite + WAL)
│   ├── models.py                # SQLAlchemy models (Setting, Repo, Event, …)
│   ├── security.py              # Authentication, password management, session handling
│   ├── github_client.py         # GitHub API client (httpx, rate-limit aware)
│   ├── utils.py                 # Shared utilities
│   ├── services/
│   │   ├── stars.py             # Starred repo sync service
│   │   ├── releases.py          # Release/tag checking service
│   │   ├── emailer.py           # Legacy SMTP wrapper (delegates to EmailNotifier)
│   │   ├── scheduler.py         # APScheduler management (4 jobs)
│   │   ├── settings.py          # Settings CRUD (encrypt/decrypt transparently)
│   │   ├── logs.py              # Application logging service
│   │   ├── notifier_manager.py  # Notifier registry & dispatch singleton
│   │   └── notifiers/
│   │       ├── base.py          # BaseNotifier abstract class
│   │       └── email.py         # EmailNotifier (SMTP implementation)
│   └── routers/
│       ├── health.py            # Health check endpoint
│       ├── auth.py              # Login/logout/change-password routes
│       ├── dashboard.py         # Dashboard stats & history
│       ├── repos.py             # Repository management routes
│       ├── events.py            # Event viewing routes
│       ├── settings_route.py    # All settings management endpoints
│       └── tasks.py             # Manual task trigger endpoints
├── frontend/
│   ├── src/                     # Vue 3 + TypeScript SPA (Vuetify 3)
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/          # Reusable components
│   │   ├── views/               # Page views (Dashboard, Repos, Events, Settings, Logs)
│   │   ├── router/              # Vue Router configuration
│   │   ├── locales/             # i18n (en, zh, ja)
│   │   ├── api/                 # API client
│   │   ├── plugins/             # Vuetify plugin setup
│   │   └── assets/              # Static assets
│   └── dist/                    # Built SPA (served by FastAPI)
├── tests/
│   ├── test_crypto.py
│   ├── test_github_client.py
│   ├── test_release_detection.py
│   ├── test_settings_encryption.py
│   └── test_settings_validation.py
├── Containerfile                # Multi-stage Podman/Docker build
├── compose.yaml                 # Docker Compose configuration
├── .dockerignore
├── pyproject.toml               # Python project dependencies & config
├── .github/workflows/ci.yml     # CI pipeline (lint, test, build frontend)
├── dev.bat                      # Windows development startup script
├── dev.ps1                      # PowerShell development startup script
├── AGENTS.md                    # Agent guide for AI-assisted development
└── README.md
```

## License

MIT
