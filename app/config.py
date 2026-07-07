"""Application configuration via pydantic-settings."""

import contextlib
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Security
    app_password: str | None = None
    session_secret: str | None = None
    app_cookie_secure: bool = False

    # Database
    database_url: str = "sqlite:////data/app.db"

    # GitHub - initial/overrides for Web UI settings
    github_username: str | None = None
    github_token: str | None = None

    # Schedule defaults
    check_schedule: str = "weekly"  # hourly, daily, weekly
    check_weekday: str = "mon"
    check_time: str = "09:00"
    monitor_prereleases: bool = False

    # Data directory
    data_dir: str = "/data"

    @property
    def database_path(self) -> str:
        """Get database URL. For sqlite, ensure directory exists."""
        if self.database_url.startswith("sqlite:///"):
            path = self.database_url.replace("sqlite:///", "")
            db_dir = Path(path).parent
            with contextlib.suppress(PermissionError):
                db_dir.mkdir(parents=True, exist_ok=True)
        return self.database_url

    def get_session_secret(self) -> str:
        """Return session secret, generating one if needed."""
        if self.session_secret:
            return self.session_secret
        self.session_secret = secrets.token_hex(32)
        return self.session_secret

    model_config = {"env_prefix": "", "case_sensitive": False, "env_file": ".env", "env_file_encoding": "utf-8"}


settings = AppSettings()
