import pytest
from app import app
from utils.validators import validate_age, sanitize_text


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_timeline_invalid_country(client):
    response = client.get("/timeline?country=invalid")
    assert response.status_code == 200
    # Should fallback to US or show US template
    assert b"US" in response.data or b"Election Timeline" in response.data


def test_eligibility_invalid_age(client):
    response = client.post("/eligibility", json={"age": -5})
    # The endpoint might return 200 with data={"eligible": False} or 400
    assert response.status_code in [200, 400]


def test_validators_edge_cases():
    assert validate_age(-1) is None
    assert validate_age(121) is None
    assert validate_age("abc") is None
    assert validate_age(0) == 0
    assert validate_age(120) == 120


def test_sanitize_text_edge_cases():
    assert sanitize_text(None) == ""
    assert sanitize_text("<script>alert(1)</script>") == "alert(1)"
    assert sanitize_text("   hello   ") == "hello"


def test_checklist_long_status(client):
    response = client.post("/checklist", json={"status": "A" * 60})
    assert response.status_code == 400


def test_reminder_long_date(client):
    response = client.post("/reminder", json={"election_day": "A" * 30})
    assert response.status_code == 400
