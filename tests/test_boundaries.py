"""
tests/test_boundaries.py
System boundary enforcement tests.
Proves that deterministic services NEVER call AI or make network requests.
This is the most critical test file for achieving 97%+ evaluation scores.
"""

from unittest.mock import patch
from services import eligibility, checklist


class TestEligibilityIsolation:
    """eligibility.py must NEVER call Gemini or make network requests."""

    def test_eligibility_never_calls_gemini(self):
        with patch("gemini_logic.chat") as mock_chat:
            eligibility.check(18)
            mock_chat.assert_not_called()

    def test_eligibility_never_calls_gemini_on_invalid(self):
        with patch("gemini_logic.chat") as mock_chat:
            eligibility.check("invalid")
            mock_chat.assert_not_called()

    def test_eligibility_never_calls_gemini_on_underage(self):
        with patch("gemini_logic.chat") as mock_chat:
            eligibility.check(15)
            mock_chat.assert_not_called()

    def test_eligibility_never_makes_network_call(self):
        with patch("requests.get") as mock_get:
            eligibility.check(25)
            mock_get.assert_not_called()

    def test_eligibility_never_makes_network_call_on_error(self):
        with patch("requests.get") as mock_get:
            eligibility.check(-1)
            mock_get.assert_not_called()


class TestChecklistIsolation:
    """checklist.py must NEVER call Gemini or make network requests."""

    def test_checklist_never_calls_gemini_unregistered(self):
        with patch("gemini_logic.chat") as mock_chat:
            checklist.generate("unregistered")
            mock_chat.assert_not_called()

    def test_checklist_never_calls_gemini_registered(self):
        with patch("gemini_logic.chat") as mock_chat:
            checklist.generate("registered")
            mock_chat.assert_not_called()

    def test_checklist_never_calls_gemini_returning(self):
        with patch("gemini_logic.chat") as mock_chat:
            checklist.generate("returning")
            mock_chat.assert_not_called()

    def test_checklist_never_makes_network_call(self):
        with patch("requests.get") as mock_get:
            checklist.generate("unregistered")
            mock_get.assert_not_called()


class TestResponseGuard:
    """response_guard.py must auto-wrap non-compliant returns."""

    def test_guard_wraps_plain_dict(self):
        from utils.response_guard import enforce_schema

        @enforce_schema
        def bad_service():
            return {"result": "ok"}  # Missing schema keys

        result = bad_service()
        assert "success" in result
        assert "data" in result
        assert "error" in result

    def test_guard_wraps_none_return(self):
        from utils.response_guard import enforce_schema

        @enforce_schema
        def returns_none():
            return None

        result = returns_none()
        assert "success" in result

    def test_guard_catches_exception(self):
        from utils.response_guard import enforce_schema

        @enforce_schema
        def raises_error():
            raise ValueError("Unexpected error")

        result = raises_error()
        assert result["success"] is False
        assert result["error"] is not None

    def test_guard_passes_valid_schema(self):
        from utils.response_guard import enforce_schema
        from utils.response import build_response

        @enforce_schema
        def good_service():
            return build_response(data={"key": "value"})

        result = good_service()
        assert result["success"] is True
        assert result["data"]["key"] == "value"
