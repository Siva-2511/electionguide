"""
tests/test_api.py
Tests for services/civic_api.py
Covers: success, mock fallback, caching, contract enforcement.
"""

import pytest
from unittest.mock import patch
from services import civic_api


# Clear cache before each test
@pytest.fixture(autouse=True)
def clear_cache():
    civic_api._civic_cache.clear()
    civic_api._last_request_times.clear()
    yield
    civic_api._civic_cache.clear()
    civic_api._last_request_times.clear()


class TestResponseContract:
    """Civic API must always return {success, data, error}."""

    def test_contract_with_no_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = civic_api.get_election_info()
        assert "success" in result
        assert "data" in result
        assert "error" in result

    def test_contract_with_api_failure(self, mock_civic_failure):
        with patch.dict("os.environ", {"GOOGLE_CIVIC_API_KEY": "fake_key"}):
            result = civic_api.get_election_info("123 Main St")
        assert "success" in result
        assert "data" in result
        assert "error" in result


class TestMockFallback:
    """Mock fallback must activate when API is unavailable."""

    def test_fallback_when_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = civic_api.get_election_info()
        assert result["success"] is True
        assert "election_name" in result["data"]
        assert "election_day" in result["data"]

    def test_fallback_on_api_failure(self, mock_civic_failure):
        with patch.dict("os.environ", {"GOOGLE_CIVIC_API_KEY": "fake_key"}):
            result = civic_api.get_election_info("Some Address")
        assert result["success"] is True
        assert "election_day" in result["data"]

    def test_fallback_has_polling_locations(self):
        with patch.dict("os.environ", {}, clear=True):
            result = civic_api.get_election_info()
        assert isinstance(result["data"]["polling_locations"], list)
        assert len(result["data"]["polling_locations"]) > 0


class TestCaching:
    """Caching must reduce redundant API calls."""

    def test_second_call_returns_cached(self):
        with patch.dict("os.environ", {}, clear=True):
            result1 = civic_api.get_election_info("DC")
            result2 = civic_api.get_election_info("DC")
        assert result1["data"]["election_day"] == result2["data"]["election_day"]

    def test_cache_is_populated_after_call(self):
        with patch.dict("os.environ", {}, clear=True):
            civic_api.get_election_info("DC")
        assert "dc" in civic_api._civic_cache


class TestCalendarIntegration:
    """Calendar reminder must be triggerable from election date."""

    def test_calendar_event_structure(self):
        from orchestrator import _add_calendar_reminder
        from unittest.mock import patch, MagicMock

        with patch("orchestrator.build_service") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.events().insert().execute.return_value = {
                "htmlLink": "https://calendar.google.com/event"
            }

            result = _add_calendar_reminder(
                "2026-11-03", "US General Election", token="dummy-token"
            )

        assert result["success"] is True
        assert "event" in result["data"]
        event = result["data"]["event"]
        assert event["start"]["date"] == "2026-11-03"
        assert "reminders" in event

    def test_calendar_returns_contract(self):
        from orchestrator import _add_calendar_reminder
        from unittest.mock import patch

        with patch("orchestrator.build_service"):
            result = _add_calendar_reminder(
                "2026-11-03", "Test Election", token="dummy-token"
            )

        assert "success" in result
        assert "data" in result
        assert "error" in result
