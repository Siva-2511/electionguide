"""
orchestrator.py

Core Pipeline Architecture for ElectionGuide.
This module chains multiple Google Services into a single, cohesive workflow.

Google Services Integrated:
1. Google Gemini API (AI routing and responses)
2. Google Civic Information API (Election data)
3. Google Calendar API (Election reminders via OAuth)
4. Google Translate (Frontend widget rendering)

app.py calls ONLY this module — never individual services directly.
"""

import logging
from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build as build_service

from utils.response import build_response
from utils.validators import (
    sanitize_text,
    check_jailbreak_attempt,
    validate_payload_size,
    validate_age,
)
import gemini_logic
from services import eligibility, checklist, civic_api
from services.india_api import get_india_election_info

logger = logging.getLogger(__name__)


def process_chat(data: Dict[str, Any]) -> Dict[str, Any]:
    """Main chat pipeline."""
    # Step 1: Input validation
    validation_error = _validate_chat_input(data)
    if validation_error:
        return validation_error

    message = sanitize_text(data.get("message", ""))
    country = sanitize_text(data.get("country", "us")).lower()
    if country not in ("us", "india", "uk", "australia", "canada"):
        country = "us"

    # Step 2: Jailbreak check
    if check_jailbreak_attempt(message):
        return _handle_jailbreak(country)

    # Step 3: Intent detection
    intent_result = gemini_logic.detect_intent(message)
    intent = intent_result.get("intent", "general")

    # Step 4: Deterministic routing (Static Intents)
    static_response = _handle_static_intents(intent, message, country)
    if static_response:
        return static_response

    # Step 5: Dynamic logic (Eligibility, Checklist, Election Info)
    extra_data, context = _handle_dynamic_logic(intent, data, country)

    # Step 6: AI response
    ai_result = gemini_logic.chat(message, context=context, country=country)
    reply = ai_result.get("data", {}).get("reply", "")

    # Step 7: Calendar logic (If requested)
    calendar_added = False
    election_day = context.get("election_day", "")
    if election_day and data.get("add_reminder"):
        cal_res = _add_calendar_reminder(election_day, context.get("election_name", "Election"), data.get("token"))
        calendar_added = cal_res.get("success", False)

    # Step 8: Final Build
    return build_response(
        success=True,
        data={
            "reply": reply,
            "intent": intent,
            "calendar_added": calendar_added,
            "election_day": election_day,
            **extra_data,
            "source": ai_result.get("source", "gemini"),
        },
    )


def _validate_chat_input(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate raw chat input."""
    message = sanitize_text(data.get("message", ""))
    if not message:
        return build_response(success=False, error="Message cannot be empty.")
    if not validate_payload_size(message):
        return build_response(
            success=False,
            error="Message is too long. Please keep your question under 500 characters.",
        )
    return None


def _handle_jailbreak(country: str) -> Dict[str, Any]:
    """Handle detected jailbreak attempts."""
    logger.warning("Jailbreak attempt blocked")
    guide = country.capitalize()
    return build_response(
        success=True,
        data={
            "reply": f"I'm here to help with {guide} election questions only.",
            "source": "security_filter",
        },
    )


def _handle_static_intents(intent: str, message: str, country: str) -> Optional[Dict[str, Any]]:
    """Handle intents that have predefined static answers."""
    responses = {
        "voter_registration": "To register in India, visit voters.eci.gov.in. For the US, visit vote.gov.",
        "voter_checklist": "Checklist: 1. Ensure you're 18+. 2. Register at voters.eci.gov.in. 3. Find booth on 'Voter Helpline'.",
    }
    if intent in responses:
        return build_response(
            success=True,
            data={"reply": responses[intent], "source": "static_intent"},
        )
    return None


def _handle_dynamic_logic(intent: str, data: Dict[str, Any], country: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Handle logic that requires external API calls or user data processing."""
    extra_data = {}
    context = {}

    if intent == "eligibility":
        age = validate_age(data.get("age", ""))
        if age is not None:
            extra_data["eligibility"] = eligibility.check(age, country=country).get("data", {})
    elif intent == "checklist":
        status = sanitize_text(data.get("status", "unregistered"))
        extra_data["checklist"] = checklist.generate(status).get("data", {})
    elif intent == "election_info":
        if country == "india":
            state = sanitize_text(data.get("state", ""))
            context = get_india_election_info(state or None).get("data", {})
        else:
            address = sanitize_text(data.get("address", ""))
            context = civic_api.get_election_info(address or None).get("data", {})
        extra_data["election_info"] = context

    return extra_data, context


def check_eligibility(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Eligibility route handler — pure deterministic logic.

    Args:
        data (Dict[str, Any]): JSON payload containing 'age' and 'country'.

    Returns:
        Dict[str, Any]: Formatted API response.
    """
    age = validate_age(data.get("age", ""))
    if age is None:
        return build_response(
            success=False,
            error="Please provide a valid age (a number between 0 and 120).",
        )
    citizen = data.get("citizen", True)
    country = sanitize_text(data.get("country", "us")).lower()
    if country not in ("us", "india", "uk", "australia", "canada"):
        country = "us"
    return eligibility.check(age, citizen=citizen, country=country)


def get_checklist(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checklist route handler — pure deterministic logic.

    Args:
        data (Dict[str, Any]): JSON payload containing 'status' and 'first_time'.

    Returns:
        Dict[str, Any]: Formatted API response with the checklist.
    """
    status = sanitize_text(data.get("status", "unregistered"))
    first_time = data.get("first_time", False)
    return checklist.generate(status=status, first_time=first_time)


def get_timeline(address: Optional[str] = None) -> Dict[str, Any]:
    """
    Timeline route handler — fetches civic data for timeline view.

    Args:
        address (Optional[str]): Street address for location-specific data.

    Returns:
        Dict[str, Any]: Formatted API response with civic data.
    """
    return civic_api.get_election_info(address)


def _add_calendar_reminder(
    election_day: str, election_name: str, token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add Election Day to Google Calendar via OAuth credentials.

    Args:
        election_day (str): The date of the election (YYYY-MM-DD).
        election_name (str): The name of the election event.
        token (Optional[str]): The OAuth access token for the user.

    Returns:
        Dict[str, Any]: Formatted API response indicating success or failure.
    """
    if not token:
        return build_response(success=False, error="Sign in first to add a reminder.")

    try:
        creds = Credentials(token=token)
        service = build_service("calendar", "v3", credentials=creds)

        event_body = {
            "summary": f"🗳️ {election_name}",
            "description": "Remember to vote! Check your polling location at vote.gov",
            "start": {"date": election_day},
            "end": {"date": election_day},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},  # 1 day before
                    {"method": "popup", "minutes": 120},  # 2 hours before
                ],
            },
        }

        # Actually insert the event into the user's primary calendar
        event = service.events().insert(calendarId="primary", body=event_body).execute()

        logger.info(
            "Calendar event created for %s: %s", election_day, event.get("htmlLink")
        )
        return build_response(
            success=True,
            data={
                "event": event_body,
                "link": event.get("htmlLink"),
                "date": election_day,
                "message": f"Calendar reminder set for {election_day}!",
            },
        )

    except Exception as e:
        logger.warning("Calendar API failed: %s", type(e).__name__)
        return build_response(success=False, error="Could not add calendar reminder.")
