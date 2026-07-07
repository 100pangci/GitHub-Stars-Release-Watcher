# GitHub Stars Release Watcher

[中文文档](./README.zh.md)

A self-hosted application to monitor your GitHub starred repositories for new releases and tags. Get weekly email summaries of all new versions from your starred projects.

## Features

- **GitHub Stars Sync**: Automatically sync your starred repositories
- **Release/Tag Monitoring**: Check each repo for new GitHub Releases and tags
- **Weekly Email Summary**: Receive a comprehensive weekly email with all new updates
- **Web UI**: Easy-to-use interface for configuration and monitoring
- **No External Dependencies**: SQLite database, no Redis/Postgres/Celery needed
- **Single Container**: Everything runs in one Podman/Docker container

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
  -e SESSION_SECRET='your-random-secret-here' \
  --restart=always \
  github-stars-release-watcher:latest
```

Then open http://localhost:8000 and log in with your password.

### Using Docker

```bash
# Build the image
docker build -t github-stars-release-watcher:latest -f Containerfile .

# Run the container
docker run -d --name github-stars-release-watcher \
  -p 8000:8000 \
  -v ./data:/data \
  -e APP_PASSWORD='your-secure-password' \
  -e SESSION_SECRET='your-random-secret-here' \
  --restart=always \
  github-stars-release-watcher:latest
```

### Using Docker Compose

```bash
# Start with docker-compose (compose.yaml is in the project root)
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down

# Rebuild and start after updating
docker compose up -d --build
```

The project includes a `compose.yaml` with the following configuration:

```yaml
version: "3.8"
services:
  watcher:
    build:
      context: .
      dockerfile: Containerfile
    container_name: github-stars-release-watcher
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    environment:
      - APP_PASSWORD=your-secure-password
      - SESSION_SECRET=your-random-secret-here
      - APP_COOKIE_SECURE=false
      - CHECK_SCHEDULE=weekly
      - CHECK_WEEKDAY=mon
      - CHECK_TIME=09:00
    restart: unless-stopped
```

You can also manage environment variables with a `.env` file:

```bash
# .env (alongside compose.yaml)
APP_PASSWORD=your-secure-password
SESSION_SECRET=your-random-secret-here
```

Then `docker compose up -d` will automatically use these values.

Then open http://localhost:8000 and log in with your password.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_PASSWORD` | No* | Auto-generated | Password for Web UI login |
| `SESSION_SECRET` | No* | Auto-generated | Secret key for session cookies |
| `APP_COOKIE_SECURE` | No | `false` | Set to `true` if using HTTPS |
| `DATABASE_URL` | No | `sqlite:////data/app.db` | Database path |
| `GITHUB_USERNAME` | No | - | GitHub username (can be set in Web UI) |
| `GITHUB_TOKEN` | No | - | GitHub Personal Access Token (can be set in Web UI) |
| `CHECK_SCHEDULE` | No | `weekly` | Check frequency: `hourly`, `daily`, `weekly` |
| `CHECK_WEEKDAY` | No | `mon` | Day for weekly checks |
| `CHECK_TIME` | No | `09:00` | Time for scheduled checks |
| `MONITOR_PRERELEASES` | No | `false` | Include prerelease versions |

*\* If not set, a random password is generated on first start and printed to the container log.*

## Setup

### 1. GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Create a new token with at least `repo` scope (for private repos) or no scope (for public repos only)
3. Copy the token and enter it in the Web UI Settings page

### 2. Configure the Application

After logging in to the Web UI:

1. **GitHub Settings**: Enter your GitHub username and Personal Access Token
2. **Schedule Settings**: Configure how often to check for releases
3. **Release/Tag Strategy**: Configure monitoring preferences
4. **Email/SMTP Settings**: Configure SMTP for weekly email summaries

### 3. Initial Sync

1. Go to Dashboard and click "Sync Stars Now" to fetch your starred repositories
2. Then click "Check Releases Now" to scan for releases

The first check will initialize the state of all repos (it will not send notifications unless `allow_initial_notifications` is enabled in settings).

## Podman Systemd Integration

To run the container as a systemd service:

```bash
# Generate a systemd unit file
podman generate systemd --new --name github-stars-release-watcher > ~/.config/systemd/user/github-stars-release-watcher.service

# Enable and start the service
systemctl --user enable --now github-stars-release-watcher.service
```

Or create a root systemd service at `/etc/systemd/system/github-stars-release-watcher.service`:

```ini
[Unit]
Description=GitHub Stars Release Watcher
After=network-online.target

[Service]
Type=simple
ExecStartPre=/usr/bin/podman pull github-stars-release-watcher:latest
ExecStart=/usr/bin/podman run --rm \
  --name github-stars-release-watcher \
  -p 8000:8000 \
  -v /opt/github-stars-release-watcher/data:/data:z \
  -e APP_PASSWORD='your-secure-password' \
  -e SESSION_SECRET='your-random-secret-here' \
  github-stars-release-watcher:latest
ExecStop=/usr/bin/podman stop -t 10 github-stars-release-watcher
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## Web UI Pages

- **Dashboard**: Overview with stats, rate limit status, and system health
- **Repositories**: Browse and search your starred repos, check individual repos
- **Events / Updates**: View detected release/tag events
- **Settings**: Configure GitHub, schedule, release strategy, and email
- **Logs**: View recent application logs

## Security Notes

- GitHub token and SMTP password are stored hashed/securely in the database
- Secrets are never displayed in the Web UI or logs
- Session cookies use HttpOnly, SameSite=Lax attributes
- All configuration changes require authentication
- CSRF protection on all POST requests
- No shell commands are executed from user input

## Development

### Prerequisites

- Python 3.12+
- pip

### Setup

```bash
# Clone the repository
cd github-stars-release-watcher

# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests

```bash
pytest
```

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # Database initialization
│   ├── models.py            # SQLAlchemy models
│   ├── security.py          # Authentication & password management
│   ├── github_client.py     # GitHub API client
│   ├── services/
│   │   ├── stars.py         # Starred repo sync service
│   │   ├── releases.py      # Release/tag checking service
│   │   ├── emailer.py       # Email sending service
│   │   ├── scheduler.py     # APScheduler management
│   │   ├── settings.py      # Settings CRUD operations
│   │   └── logs.py          # Application logging
│   ├── routers/
│   │   ├── health.py        # Health check endpoint
│   │   ├── auth.py          # Login/logout routes
│   │   ├── dashboard.py     # Dashboard routes
│   │   ├── repos.py         # Repository management routes
│   │   ├── events.py        # Event viewing routes
│   │   ├── settings.py      # Settings management routes
│   │   └── tasks.py         # Manual task trigger routes
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS and static assets
├── tests/
│   ├── test_github_client.py
│   ├── test_release_detection.py
│   └── test_settings_validation.py
├── Containerfile            # Podman/Docker build file
├── compose.yaml             # Docker Compose configuration
├── pyproject.toml           # Python project configuration
└── README.md
```

## License

MIT