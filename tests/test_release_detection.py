"""Tests for release detection logic."""

from app.utils import parse_dt


class TestReleaseDetection:
    """Tests for release detection utilities."""

    def test_parse_dt_valid(self):
        """Test parsing valid ISO datetime."""
        result = parse_dt("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.tzinfo is not None

    def test_parse_dt_no_tz(self):
        """Test parsing datetime without timezone."""
        result = parse_dt("2024-01-15T10:30:00")
        assert result is not None
        assert result.tzinfo is not None  # Should be made UTC

    def test_parse_dt_none(self):
        """Test parsing None."""
        result = parse_dt(None)
        assert result is None

    def test_parse_dt_empty(self):
        """Test parsing empty string."""
        result = parse_dt("")
        assert result is None

    def test_parse_dt_invalid(self):
        """Test parsing invalid string."""
        result = parse_dt("not-a-date")
        assert result is None
