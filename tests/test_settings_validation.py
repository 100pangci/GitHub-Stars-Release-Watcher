"""Tests for settings validation logic."""

from app.services.settings import validate_github_username, validate_port


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_validate_port_valid(self):
        """Test valid port numbers."""
        assert validate_port("587") is True
        assert validate_port("25") is True
        assert validate_port("465") is True
        assert validate_port("1") is True
        assert validate_port("65535") is True

    def test_validate_port_invalid(self):
        """Test invalid port numbers."""
        assert validate_port("0") is False
        assert validate_port("70000") is False
        assert validate_port("abc") is False
        assert validate_port("") is False
        assert validate_port(None) is False

    def test_validate_username_valid(self):
        """Test valid GitHub usernames."""
        assert validate_github_username("octocat") is True
        assert validate_github_username("user-name") is True
        assert validate_github_username("user123") is True
        assert validate_github_username("a") is True

    def test_validate_username_invalid(self):
        """Test invalid GitHub usernames."""
        assert validate_github_username("") is False
        assert validate_github_username("user name") is False
        assert validate_github_username("user@name") is False
        assert validate_github_username(None) is False
        # Name too long (over 39 chars)
        assert validate_github_username("a" * 40) is False


