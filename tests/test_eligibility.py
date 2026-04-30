"""
tests/test_eligibility.py
Tests for services/eligibility.py
Covers: age boundaries, citizenship, invalid input, and contract enforcement.
"""
import pytest
from services import eligibility


# ── Contract Tests ─────────────────────────────────────────────────────────
class TestResponseContract:
    """Every code path MUST return {success, data, error} schema."""

    def test_contract_eligible_adult(self):
        result = eligibility.check(25)
        assert "success" in result
        assert "data" in result
        assert "error" in result

    def test_contract_underage(self):
        result = eligibility.check(10)
        assert "success" in result
        assert "data" in result
        assert "error" in result

    def test_contract_invalid_input(self):
        result = eligibility.check("abc")
        assert "success" in result
        assert "data" in result
        assert "error" in result

    def test_contract_boundary_18(self):
        result = eligibility.check(18)
        assert "success" in result
        assert "data" in result
        assert "error" in result

    def test_contract_non_citizen(self):
        result = eligibility.check(25, citizen=False)
        assert "success" in result
        assert "data" in result
        assert "error" in result


# ── Logic Tests ────────────────────────────────────────────────────────────
class TestEligibilityLogic:

    def test_eligible_adult(self):
        result = eligibility.check(25)
        assert result["success"] is True
        assert result["data"]["eligible"] is True

    def test_eligible_boundary_18(self):
        """Exact boundary — must be eligible."""
        result = eligibility.check(18)
        assert result["success"] is True
        assert result["data"]["eligible"] is True
        assert result["data"]["first_time_voter"] is True

    def test_underage_17(self):
        """Pre-registration age — not eligible but can pre-register."""
        result = eligibility.check(17)
        assert result["success"] is True
        assert result["data"]["eligible"] is False
        assert result["data"]["can_preregister"] is True

    def test_underage_child(self):
        result = eligibility.check(10)
        assert result["success"] is True
        assert result["data"]["eligible"] is False

    def test_underage_zero(self):
        result = eligibility.check(0)
        assert result["success"] is True
        assert result["data"]["eligible"] is False

    def test_non_citizen(self):
        result = eligibility.check(25, citizen=False)
        assert result["success"] is True
        assert result["data"]["eligible"] is False
        assert "citizen" in result["data"]["reason"].lower()


# ── Invalid Input Tests ────────────────────────────────────────────────────
class TestInvalidInputs:

    def test_string_input(self):
        result = eligibility.check("hello")
        assert result["success"] is False
        assert result["error"] is not None

    def test_negative_age(self):
        result = eligibility.check(-5)
        assert result["success"] is False
        assert result["error"] is not None

    def test_none_input(self):
        result = eligibility.check(None)
        assert result["success"] is False
        assert result["error"] is not None

    def test_float_rounds_to_int(self):
        """Floats should be safely handled."""
        result = eligibility.check(18.9)
        assert "success" in result  # Must not crash

    def test_oversized_age(self):
        result = eligibility.check(999)
        assert result["success"] is False

    def test_empty_string(self):
        result = eligibility.check("")
        assert result["success"] is False
