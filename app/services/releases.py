"""Release and tag checking service."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.github_client import GitHubClient
from app.models import Event, Repo, RepoState, Version
from app.services.logs import add_log
from app.services.settings import get_setting
from app.utils import parse_dt

logger = logging.getLogger(__name__)


async def check_releases(token: str, delay: float = 0.2, db: Session | None = None) -> dict:
    """Check all active repos for new releases/tags."""
    should_close = db is None
    if db is None:
        db = SessionLocal()

    try:
        # Get settings
        monitor_prereleases = get_setting(db, "monitor_prereleases", "false").lower() == "true"
        fallback_to_tags = get_setting(db, "fallback_to_tags", "true").lower() == "true"
        ignore_archived = get_setting(db, "ignore_archived", "true").lower() == "true"
        allow_initial = get_setting(db, "allow_initial_notifications", "false").lower() == "true"

        client = GitHubClient(token=token, delay=delay)

        # Get all active (non-archived) repos
        query = db.query(Repo).filter(Repo.active == True)  # noqa: E712
        if ignore_archived:
            query = query.filter(Repo.archived == False)  # noqa: E712
        repos = query.all()

        checked = 0
        updated = 0
        errors = 0
        now = datetime.now(UTC)

        for repo in repos:
            try:
                owner, name = repo.full_name.split("/", 1)
            except ValueError:
                errors += 1
                continue

            try:
                result = await _check_single_repo(
                    client, db, repo, owner, name,
                    monitor_prereleases, fallback_to_tags, allow_initial, now,
                )
                if result:
                    updated += 1
                checked += 1
                await asyncio.sleep(delay)
            except Exception as e:
                logger.warning(f"Error checking {repo.full_name}: {e}")
                errors += 1
                await asyncio.sleep(delay)

        db.commit()

        message = f"Checked {checked} repos: {updated} updates, {errors} errors"
        add_log("INFO", message, db=db)
        logger.info(message)

        return {
            "checked": checked,
            "updates": updated,
            "errors": errors,
            "rate_limit_remaining": client.rate_limit_remaining,
        }
    except Exception as e:
        db.rollback()
        add_log("ERROR", f"Release check failed: {e}", db=db)
        logger.exception("Release check failed")
        raise
    finally:
        if should_close:
            db.close()


async def _check_single_repo(
    client: GitHubClient,
    db: Session,
    repo: Repo,
    owner: str,
    name: str,
    monitor_prereleases: bool,
    fallback_to_tags: bool,
    allow_initial: bool,
    now: datetime,
) -> bool:
    """Check a single repo for new version. Returns True if update found."""
    # Get or create state
    state = db.query(RepoState).filter(RepoState.repo_id == repo.id).first()
    if state is None:
        state = RepoState(repo_id=repo.id, initialized=False)
        db.add(state)
        db.flush()

    # Get latest release
    release = None

    if monitor_prereleases:
        releases = await client.get_releases(owner, name, per_page=10)
        release = releases[0] if releases else None
    else:
        release = await client.get_latest_release(owner, name)

    version_found = None
    if release:
        tag_name = release.get("tag_name", "")
        version_found = {
            "source": "release",
            "version": tag_name,
            "release_name": release.get("name", "") or tag_name,
            "html_url": release.get("html_url", ""),
            "published_at": parse_dt(release.get("published_at")),
            "is_prerelease": bool(release.get("prerelease", False)),
        }

    # Fallback to tags if no release found
    if version_found is None and fallback_to_tags:
        tag = await client.get_latest_tag(owner, name)
        if tag:
            version_found = {
                "source": "tag",
                "version": tag.get("name", ""),
                "release_name": tag.get("name", ""),
                "html_url": f"{repo.html_url}/releases/tag/{tag.get('name', '')}",
                "published_at": parse_dt(tag.get("commit", {}).get("commit", {}).get("author", {}).get("date")),
                "is_prerelease": False,
            }

    if version_found is None:
        # No releases or tags
        repo.last_checked_at = now
        return False

    # Check if this version is already recorded
    existing_version = db.query(Version).filter(
        Version.repo_id == repo.id,
        Version.source == version_found["source"],
        Version.version == version_found["version"],
    ).first()

    is_new = existing_version is None

    if is_new:
        # Create version record
        ver = Version(
            repo_id=repo.id,
            source=version_found["source"],
            version=version_found["version"],
            release_name=version_found["release_name"],
            html_url=version_found["html_url"],
            published_at=version_found["published_at"],
            seen_at=now,
            is_prerelease=version_found["is_prerelease"],
        )
        db.add(ver)
        db.flush()

        # Only create event if initialized or allow_initial
        if state.initialized or allow_initial:
            event = Event(
                repo_id=repo.id,
                version_id=ver.id,
                event_type="new_release",
                title=f"{repo.full_name}: {version_found['version']}",
                message=f"New {version_found['source']}: {version_found['version']}",
                created_at=now,
            )
            db.add(event)

        # Update state
        state.current_source = version_found["source"]
        state.current_version = version_found["version"]
        state.current_version_url = version_found["html_url"]
        state.current_published_at = version_found["published_at"]
        state.initialized = True

        repo.last_checked_at = now
        logger.info(f"New {version_found['source']} for {repo.full_name}: {version_found['version']}")
        return True
    else:
        # Already known version, just update check time
        repo.last_checked_at = now
        # Still ensure initialized
        if not state.initialized:
            state.initialized = True
        return False


