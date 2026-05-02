"""
tests/test_chatbot.py
Tests for gemini_logic.py
Covers: intent detection, output filter, readability enforcer, fallback behavior.
"""
import pytest
from unittest.mock import patch, MagicMock
import gemini_logic


class TestIntentDetection:
    """Intent detection uses no AI — purely keyword-based."""

    def test_intent_eligibility(self):
        result = gemini_logic.detect_intent("Can I vote? I am 18 years old.")
        assert result["intent"] == "eligibility"

    def test_intent_checklist_how_to(self):
        result = gemini_logic.detect_intent("How do I vote? What are the steps?")
        assert result["intent"] == "voter_checklist"

    def test_intent_election_info(self):
        result = gemini_logic.detect_intent("When is election day in my state?")
        assert result["intent"] == "general"

    def test_intent_registration(self):
        result = gemini_logic.detect_intent("How do I register to vote?")
        assert result["intent"] == "voter_registration"

    def test_intent_general(self):
        result = gemini_logic.detect_intent("Hello there")
        assert result["intent"] == "general"

    def test_intent_empty(self):
        result = gemini_logic.detect_intent("")
        assert "intent" in result  # Must not crash


class TestOutputFilter:
    """Output filter must block biased/political content."""

    def test_blocks_political_party(self):
        result = gemini_logic.filter_output("You should vote for the Republican party.")
        assert result == gemini_logic.SAFE_FALLBACK

    def test_blocks_candidate_name(self):
        result = gemini_logic.filter_output("Trump is the best choice.")
        assert result == gemini_logic.SAFE_FALLBACK

    def test_blocks_persuasion(self):
        result = gemini_logic.filter_output("You should vote for this candidate.")
        assert result == gemini_logic.SAFE_FALLBACK

    def test_allows_clean_civic_content(self):
        clean = "You can register to vote at vote.gov. Bring a valid ID on election day."
        result = gemini_logic.filter_output(clean)
        assert result == clean

    def test_handles_empty_input(self):
        result = gemini_logic.filter_output("")
        assert result == ""

    def test_handles_none(self):
        result = gemini_logic.filter_output(None)
        assert result == ""


class TestReadabilityEnforcer:
    """Readability enforcer must be testable and consistent."""

    def test_converts_long_text_to_bullets(self):
        long_text = " ".join([
            "First sentence.", "Second sentence.", "Third sentence.",
            "Fourth sentence.", "Fifth sentence.", "Sixth sentence."
        ])
        result = gemini_logic.enforce_readability(long_text)
        assert "•" in result

    def test_preserves_short_content(self):
        short = "Register to vote at vote.gov."
        result = gemini_logic.enforce_readability(short)
        assert short in result

    def test_handles_empty(self):
        result = gemini_logic.enforce_readability("")
        assert result == ""

    def test_strips_excess_whitespace(self):
        messy = "  Hello   \n\n\n  World  "
        result = gemini_logic.enforce_readability(messy)
        assert "   " not in result


class TestGeminiFallback:
    """Gemini must always return safe fallback when API fails."""

    def test_gemini_failure_returns_fallback(self, mock_gemini_failure):
        result = gemini_logic.chat("How do I vote?")
        assert result["success"] is True
        assert "reply" in result["data"]
        assert result["data"]["source"] == "fallback"

    def test_empty_message_does_not_crash(self):
        """Even empty strings should not cause exceptions."""
        result = gemini_logic.chat("")
        assert "success" in result

    def test_chat_contract(self, mock_gemini_success):
        result = gemini_logic.chat("How do I register?")
        assert "success" in result
        assert "data" in result
        assert "error" in result
