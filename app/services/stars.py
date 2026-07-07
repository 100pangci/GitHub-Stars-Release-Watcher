"""GitHub stars synchronization service."""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.github_client import GitHubClient
from app.models import Repo, RepoState
from app.services.logs import add_log
from app.utils import parse_dt

logger = logging.getLogger(__name__)


async def sync_stars(username: str, token: str, delay: float = 0.2, db: Session | None = None) -> dict:
    """Sync starred repositories from GitHub."""
    should_close = db is None
    if db is None:
        db = SessionLocal()

    try:
        client = GitHubClient(token=token, delay=delay)
        repos_data = await client.get_starred_repos(username)

        synced = 0
        new_repos = 0
        unstarred = 0
        now = datetime.now(UTC)

        # Track which full_names we see from API
        seen_full_names = set()

        for repo_data in repos_data:
            full_name = repo_data.get("full_name", "")
            if not full_name:
                continue
            seen_full_names.add(full_name)

            # Parse fields
            pushed_at = parse_dt(repo_data.get("pushed_at"))
            starred_at = parse_dt(repo_data.get("starred_at"))

            # Check if repo exists
            existing = db.query(Repo).filter(Repo.full_name == full_name).first()
            if existing:
                # Update fields
                existing.owner = repo_data.get("owner", {}).get("login", "")
                existing.name = repo_data.get("name", "")
                existing.html_url = repo_data.get("html_url", "")
                existing.description = repo_data.get("description", "") or ""
                existing.language = repo_data.get("language") or ""
                existing.archived = bool(repo_data.get("archived", False))
                existing.disabled = bool(repo_data.get("disabled", False))
                existing.private = bool(repo_data.get("private", False))
                existing.pushed_at = pushed_at
                if starred_at:
                    existing.starred_at = starred_at
                existing.last_synced_at = now

                # Re-activate if was inactive
                if not existing.active:
                    existing.active = True
                    logger.info(f"Re-activated repo: {full_name}")

                synced += 1
            else:
                # New repo
                repo = Repo(
                    full_name=full_name,
                    owner=repo_data.get("owner", {}).get("login", ""),
                    name=repo_data.get("name", ""),
                    html_url=repo_data.get("html_url", ""),
                    description=repo_data.get("description", "") or "",
                    language=repo_data.get("language") or "",
                    archived=bool(repo_data.get("archived", False)),
                    disabled=bool(repo_data.get("disabled", False)),
                    private=bool(repo_data.get("private", False)),
                    active=True,
                    pushed_at=pushed_at,
                    starred_at=starred_at,
                    last_synced_at=now,
                )
                db.add(repo)
                db.flush()

                # Create RepoState
                state = RepoState(repo_id=repo.id, initialized=False)
                db.add(state)

                new_repos += 1
                synced += 1

            db.flush()

        # Mark repos not in API response as inactive
        active_repos = db.query(Repo).filter(Repo.active == True).all()  # noqa: E712
        for repo in active_repos:
            if repo.full_name not in seen_full_names:
                repo.active = False
                repo.last_synced_at = now
                logger.info(f"Marked {repo.full_name} as inactive (unstarred)")
                unstarred += 1

        db.commit()

        message = f"Synced {synced} repos ({new_repos} new, {unstarred} unstarred)"
        add_log("INFO", message, db=db)
        logger.info(message)

        return {
            "synced": synced,
            "new": new_repos,
            "unstarred": unstarred,
            "rate_limit_remaining": client.rate_limit_remaining,
            "rate_limit_limit": client.rate_limit_limit,
        }
    except ValueError as e:
        db.rollback()
        add_log("ERROR", f"Stars sync failed: {e}", db=db)
        raise
    except Exception as e:
        db.rollback()
        add_log("ERROR", f"Stars sync failed: {e}", db=db)
        logger.exception("Stars sync failed")
        raise
    finally:
        if should_close:
            db.close()


