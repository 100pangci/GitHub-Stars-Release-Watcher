"""Tests for GitHub API client."""
import pytest
from datetime import datetime, timezone

from app.github_client import GitHubClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization with token."""
    client = GitHubClient(token="test-token", delay=0.0)
    assert client.token == "test-token"
    assert client.delay == 0.0
    assert client.rate_limit_remaining == 5000


def test_client_headers():
    """Test request headers."""
    client = GitHubClient(token="test-token")
    headers = client._headers()
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Accept"] == "application/vnd.github+json"
    assert headers["X-GitHub-Api-Version"] == "2022-11-28"
    assert headers["User-Agent"] == "github-stars-release-watcher"


def test_client_headers_no_token():
    """Test headers when no token is set."""
    client = GitHubClient(token="")
    headers = client._headers()
    assert "Authorization" not in headers


def test_rate_limit_update():
    """Test rate limit info extraction from response headers."""
    from unittest.mock import MagicMock

    client = GitHubClient(token="test")
    response = MagicMock()
    response.headers = {
        "X-RateLimit-Remaining": "42",
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Reset": "1700000000",
    }

    client._update_rate_limit(response)
    assert client.rate_limit_remaining == 42
    assert client.rate_limit_limit == 5000
    assert client.rate_limit_reset is not None