"""SQLAlchemy ORM models."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.now(UTC)


class Setting(Base):
    """Key-value settings store with secret flag."""

    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, default="")
    secret = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    def __repr__(self):
        return f"<Setting {self.key}>"


class Repo(Base):
    """GitHub repository metadata."""

    __tablename__ = "repos"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), unique=True, nullable=False, index=True)
    owner = Column(String(128), default="")
    name = Column(String(128), default="")
    html_url = Column(String(512), default="")
    description = Column(Text, default="")
    language = Column(String(64), default="")
    archived = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)
    private = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    pushed_at = Column(DateTime, nullable=True)
    starred_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    versions = relationship("Version", back_populates="repo", cascade="all, delete-orphan")
    state = relationship("RepoState", back_populates="repo", uselist=False, cascade="all, delete-orphan")
    events = relationship("Event", back_populates="repo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repo {self.full_name}>"


class Version(Base):
    """Recorded release/tag version."""

    __tablename__ = "versions"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    source = Column(String(16), nullable=False)  # 'release' or 'tag'
    version = Column(String(255), nullable=False)
    release_name = Column(String(255), default="")
    html_url = Column(String(512), default="")
    published_at = Column(DateTime, nullable=True)
    seen_at = Column(DateTime, default=_now)
    is_prerelease = Column(Boolean, default=False)

    repo = relationship("Repo", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("repo_id", "source", "version", name="uq_repo_source_version"),
    )

    def __repr__(self):
        return f"<Version {self.version} ({self.source})>"


class RepoState(Base):
    """Current state of a repository's latest known version."""

    __tablename__ = "repo_state"

    repo_id = Column(Integer, ForeignKey("repos.id"), primary_key=True, unique=True)
    current_source = Column(String(16), default="")
    current_version = Column(String(255), default="")
    current_version_url = Column(String(512), default="")
    current_published_at = Column(DateTime, nullable=True)
    initialized = Column(Boolean, default=False)

    repo = relationship("Repo", back_populates="state")

    def __repr__(self):
        return f"<RepoState {self.repo_id}: {self.current_version}>"


class Event(Base):
    """Events created when new versions are detected."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("versions.id"), nullable=True)
    event_type = Column(String(32), default="new_release")
    title = Column(String(255), default="")
    message = Column(Text, default="")
    created_at = Column(DateTime, default=_now)
    included_in_weekly_summary = Column(Boolean, default=False)

    repo = relationship("Repo", back_populates="events")
    version = relationship("Version", foreign_keys=[version_id])

    def __repr__(self):
        return f"<Event {self.event_type}: {self.title}>"


class TaskRun(Base):
    """Background task execution records."""

    __tablename__ = "task_runs"

    id = Column(Integer, primary_key=True)
    task_name = Column(String(64), nullable=False, index=True)
    status = Column(String(16), default="running")  # running, completed, failed, skipped
    started_at = Column(DateTime, default=_now)
    finished_at = Column(DateTime, nullable=True)
    message = Column(Text, default="")
    checked_repos = Column(Integer, default=0)
    found_updates = Column(Integer, default=0)

    def __repr__(self):
        return f"<TaskRun {self.task_name}: {self.status}>"


class AppLog(Base):
    """Application log entries."""

    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True)
    level = Column(String(16), default="INFO")
    message = Column(Text, default="")
    created_at = Column(DateTime, default=_now)

    def __repr__(self):
        return f"<AppLog {self.level}: {self.message[:50]}>"
