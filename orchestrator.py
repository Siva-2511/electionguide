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
import os
import logging
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


def process_chat(data: dict) -> dict:
    """
    Main chat pipeline.
    Flow: validate → jailbreak check → intent → context fetch → AI → filter → translate → respond

    Args:
        data: dict with 'message', optional 'lang', 'address', 'age', 'status'

    Returns:
        build_response() with final reply and metadata
    """
    # --- Step 1: Input validation ---
    raw_message = data.get("message", "")
    message = sanitize_text(raw_message)
    lang = sanitize_text(data.get("lang", "en"))
    address = sanitize_text(data.get("address", ""))
    country = sanitize_text(data.get("country", "us")).lower()
    if country not in ("us", "india", "uk", "australia", "canada"):
        country = "us"

    if not message:
        return build_response(
            success=False,
            error="Message cannot be empty."
        )

    if not validate_payload_size(message):
        return build_response(
            success=False,
            error="Message is too long. Please keep your question under 500 characters."
        )

    # --- Step 2: Jailbreak check ---
    if check_jailbreak_attempt(message):
        logger.warning("Jailbreak attempt blocked")
        guide = country.capitalize()
        return build_response(
            success=True,
            data={
                "reply": f"I'm here to help with {guide} election questions only. What would you like to know about voting?",
                "source": "security_filter"
            }
        )

    # --- Step 3: Intent detection (lightweight, no AI) ---
    intent_result = gemini_logic.detect_intent(message)
    intent = intent_result.get("intent", "general")

    # --- Step 4: Deterministic routing (no AI for logic) ---
    context = {}
    extra_data = {}
    
    # Handle explicit intents (Civic Data / Snappy Answers)
    if intent == 'voter_registration':
        return "To register in India, visit voters.eci.gov.in. You'll need your age proof and address proof. For the US, visit vote.gov."
    
    if intent == 'voter_checklist':
        return "Your Voter Checklist: 1. Check eligibility (18+), 2. Register on the electoral roll, 3. Find your polling booth, 4. Carry your EPIC card/Identity proof on election day."

    if intent == 'eligibility':
        age = validate_age(data.get("age", ""))
        if age is not None:
            # India min age is also 18 — same deterministic check
            elig_result = eligibility.check(age, country=country)
            extra_data["eligibility"] = elig_result.get("data", {})

    elif intent == "checklist":
        status = sanitize_text(data.get("status", "unregistered"))
        checklist_result = checklist.generate(status)
        extra_data["checklist"] = checklist_result.get("data", {})

    elif intent == "election_info":
        if country == "india":
            state = sanitize_text(data.get("state", ""))
            civic_result = get_india_election_info(state or None)
        else:
            civic_result = civic_api.get_election_info(address or None)
        context = civic_result.get("data", {})
        extra_data["election_info"] = context

    # --- Step 5: AI response (country-aware) ---
    ai_result = gemini_logic.chat(message, context=context, country=country)
    reply = ai_result.get("data", {}).get("reply", "")

    # --- Step 6: Calendar trigger (FORCED if election date is in context) ---
    calendar_added = False
    election_day = context.get("election_day", "")
    if election_day and data.get("add_reminder", False):
        cal_result = _add_calendar_reminder(
            election_day=election_day,
            election_name=context.get("election_name", "Election Day")
        )
        calendar_added = cal_result.get("success", False)

    # --- Step 7: Build final response ---
    return build_response(
        success=True,
        data={
            "reply": reply,
            "intent": intent,
            "calendar_added": calendar_added,
            "election_day": election_day,
            **extra_data
        }
    )


def check_eligibility(data: dict) -> dict:
    """
    Eligibility route handler — pure deterministic, no AI.
    Passes country so response text is country-specific.
    """
    age = validate_age(data.get("age", ""))
    if age is None:
        return build_response(
            success=False,
            error="Please provide a valid age (a number between 0 and 120)."
        )
    citizen = data.get("citizen", True)
    country = sanitize_text(data.get("country", "us")).lower()
    if country not in ("us", "india", "uk", "australia", "canada"):
        country = "us"
    return eligibility.check(age, citizen=citizen, country=country)


def get_checklist(data: dict) -> dict:
    """
    Checklist route handler — pure deterministic, no AI.
    """
    status = sanitize_text(data.get("status", "unregistered"))
    first_time = data.get("first_time", False)
    return checklist.generate(status=status, first_time=first_time)


def get_timeline(address: str = None) -> dict:
    """
    Timeline route handler — fetches civic data for timeline view.
    """
    return civic_api.get_election_info(address)


def _add_calendar_reminder(election_day: str, election_name: str, token: str = None) -> dict:
    """
    Add Election Day to Google Calendar via OAuth credentials.
    Uses google-api-python-client with OAuth flow.
    """
    if not token:
        return build_response(success=False, error="Sign in first to add a reminder.")

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build as build_service

        creds = Credentials(token=token)
        service = build_service('calendar', 'v3', credentials=creds)

        event_body = {
            "summary": f"🗳️ {election_name}",
            "description": "Remember to vote! Check your polling location at vote.gov",
            "start": {"date": election_day},
            "end": {"date": election_day},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},  # 1 day before
                    {"method": "popup", "minutes": 120}    # 2 hours before
                ]
            }
        }

        # Actually insert the event into the user's primary calendar
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        
        logger.info("Calendar event created for %s: %s", election_day, event.get('htmlLink'))
        return build_response(
            success=True,
            data={
                "event": event_body, 
                "link": event.get('htmlLink'), 
                "date": election_day,
                "message": f"Calendar reminder set for {election_day}!"
            }
        )

    except Exception as e:
        logger.warning("Calendar API failed: %s", type(e).__name__)
        return build_response(success=False, error="Could not add calendar reminder.")
