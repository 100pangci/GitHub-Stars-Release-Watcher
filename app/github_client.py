"""GitHub API client for interacting with GitHub REST API."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "github-stars-release-watcher"
DEFAULT_TIMEOUT = 30.0


class GitHubClient:
    """Client for GitHub REST API with rate limit tracking and global throttling."""

    def __init__(self, token: str, delay: float = 0.2):
        self.token = token
        self.delay = delay
        self.rate_limit_remaining: int = 5000
        self.rate_limit_limit: int = 5000
        self.rate_limit_reset: datetime | None = None
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def _throttle(self):
        """Ensure minimum delay between consecutive API requests."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _update_rate_limit(self, response: httpx.Response):
        """Update rate limit info from response headers."""
        try:
            remaining = response.headers.get("X-RateLimit-Remaining")
            limit = response.headers.get("X-RateLimit-Limit")
            reset = response.headers.get("X-RateLimit-Reset")
            if remaining is not None:
                self.rate_limit_remaining = int(remaining)
            if limit is not None:
                self.rate_limit_limit = int(limit)
            if reset is not None:
                self.rate_limit_reset = datetime.fromtimestamp(int(reset), tz=UTC)
        except (ValueError, TypeError):
            pass

    async def _request(self, url: str, params: dict | None = None) -> httpx.Response:
        """Make an HTTP GET request with timeout, throttling, and rate limit tracking."""
        await self._throttle()
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=self._headers(), params=params)
            self._update_rate_limit(response)

            if response.status_code == 403 and self.rate_limit_remaining == 0:
                ts = self.rate_limit_reset
                reset_time = ts.strftime("%Y-%m-%d %H:%M:%S UTC") if ts else "unknown"
                raise RuntimeError(f"GitHub API rate limit exhausted. Resets at {reset_time}")
            if response.status_code == 401:
                raise RuntimeError("GitHub API authentication failed. Check your token.")
            if response.status_code == 404:
                return response  # Not found is handled by caller
            if response.status_code >= 500:
                raise RuntimeError(f"GitHub API server error: {response.status_code}")

            response.raise_for_status()
            return response

    async def get_starred_repos(self, username: str) -> list[dict[str, Any]]:
        """Get all starred repositories for a user with pagination."""
        repos = []
        page = 1

        while True:
            url = f"{GITHUB_API_BASE}/users/{username}/starred"
            response = await self._request(url, params={"per_page": 100, "page": page})

            if response.status_code == 404:
                raise RuntimeError(f"GitHub user '{username}' not found")

            data = response.json()
            if not data:
                break

            repos.extend(data)
            page += 1

            # Check if there are more pages
            link_header = response.headers.get("Link", "")
            if 'rel="next"' not in link_header:
                break

            # Respect rate limiting
            await asyncio.sleep(self.delay)

        logger.info(f"Fetched {len(repos)} starred repos for user '{username}'")
        return repos

    async def get_latest_release(self, owner: str, repo: str) -> dict | None:
        """Get the latest release for a repository."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases/latest"
        try:
            response = await self._request(url)
            if response.status_code == 404:
                return None
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_releases(self, owner: str, repo: str, per_page: int = 10) -> list[dict]:
        """Get recent releases for a repository."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases"
        try:
            response = await self._request(url, params={"per_page": per_page})
            if response.status_code == 404:
                return []
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise

    async def get_latest_tag(self, owner: str, repo: str) -> dict | None:
        """Get the latest tag for a repository."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/tags"
        try:
            response = await self._request(url, params={"per_page": 1})
            if response.status_code == 404:
                return None
            data = response.json()
            return data[0] if data else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def check_rate_limit(self) -> dict[str, Any]:
        """Check current rate limit status."""
        url = f"{GITHUB_API_BASE}/rate_limit"
        try:
            response = await self._request(url)
            data = response.json()
            if "resources" in data and "core" in data["resources"]:
                self.rate_limit_remaining = data["resources"]["core"]["remaining"]
                self.rate_limit_limit = data["resources"]["core"]["limit"]
                reset_ts = data["resources"]["core"].get("reset", 0)
                if reset_ts:
                    self.rate_limit_reset = datetime.fromtimestamp(reset_ts, tz=UTC)
            return {
                "remaining": self.rate_limit_remaining,
                "limit": self.rate_limit_limit,
                "reset": self.rate_limit_reset,
            }
        except Exception as e:
            logger.warning(f"Failed to check rate limit: {e}")
            return {"remaining": self.rate_limit_remaining, "limit": self.rate_limit_limit, "reset": None}
