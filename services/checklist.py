"""
services/checklist.py
Dynamic voter roadmap generator.
ZERO AI calls. ZERO network calls. Always returns build_response() schema.
"""

from typing import Dict, Any, List
from utils.response import build_response
from utils.response_guard import enforce_schema

# Voter status types
STATUS_UNREGISTERED = "unregistered"
STATUS_REGISTERED = "registered"
STATUS_RETURNING = "returning"


@enforce_schema
def generate(
    status: str = STATUS_UNREGISTERED, first_time: bool = False
) -> Dict[str, Any]:
    """Generate a personalized voter checklist based on registration status.

    Args:
        status (str): "unregistered", "registered", or "returning". Defaults to "unregistered".
        first_time (bool): Whether user is a first-time voter. Defaults to False.

    Returns:
        Dict[str, Any]: build_response() with ordered checklist steps.
    """
    status = status.lower().strip() if status else STATUS_UNREGISTERED

    if status == STATUS_UNREGISTERED or first_time:
        steps = _full_steps()
    elif status == STATUS_REGISTERED:
        steps = _registered_steps()
    elif status == STATUS_RETURNING:
        steps = _returning_steps()
    else:
        steps = _full_steps()

    return build_response(
        success=True,
        data={
            "status": status,
            "total_steps": len(steps),
            "steps": steps,
            "resource": "https://vote.gov",
        },
    )


def _full_steps() -> List[Dict[str, Any]]:
    """Full checklist for first-time or unregistered voters.

    Returns:
        List[Dict[str, Any]]: A list of checklist steps.
    """
    return [
        {
            "step": 1,
            "title": "Check Your Eligibility",
            "description": "Make sure you are 18+ and a US citizen.",
            "action": "Use our Eligibility Checker above.",
            "done": False,
        },
        {
            "step": 2,
            "title": "Register to Vote",
            "description": "Register online, by mail, or in person.",
            "action": "Visit vote.gov to register in minutes.",
            "done": False,
        },
        {
            "step": 3,
            "title": "Confirm Your Registration",
            "description": "Check that your registration was accepted.",
            "action": "Visit vote.org/am-i-registered-to-vote/",
            "done": False,
        },
        {
            "step": 4,
            "title": "Find Your Polling Location",
            "description": "Know exactly where to go on Election Day.",
            "action": "Enter your address in our Election Info panel.",
            "done": False,
        },
        {
            "step": 5,
            "title": "Prepare Your ID",
            "description": "Most states require a valid photo ID to vote.",
            "action": "Check your state's ID requirements at ncsl.org.",
            "done": False,
        },
        {
            "step": 6,
            "title": "Set an Election Day Reminder",
            "description": "Don't forget — add it to your calendar now.",
            "action": "Click 'Add Reminder' to save Election Day.",
            "done": False,
        },
        {
            "step": 7,
            "title": "Vote on Election Day",
            "description": "Go to your polling location and cast your ballot.",
            "action": "Polls are typically open 6 AM – 8 PM.",
            "done": False,
        },
    ]


def _registered_steps() -> List[Dict[str, Any]]:
    """Shorter checklist for already-registered voters.

    Returns:
        List[Dict[str, Any]]: A list of checklist steps.
    """
    return [
        {
            "step": 1,
            "title": "Confirm Your Registration is Active",
            "description": "Check your registration hasn't lapsed.",
            "action": "Visit vote.org/am-i-registered-to-vote/",
            "done": False,
        },
        {
            "step": 2,
            "title": "Find Your Polling Location",
            "description": "Your assigned polling place may have changed.",
            "action": "Enter your address in our Election Info panel.",
            "done": False,
        },
        {
            "step": 3,
            "title": "Prepare Your ID",
            "description": "Bring a valid photo ID on Election Day.",
            "action": "Check your state's ID requirements at ncsl.org.",
            "done": False,
        },
        {
            "step": 4,
            "title": "Set a Reminder",
            "description": "Add Election Day to your calendar.",
            "action": "Click 'Add Reminder' below.",
            "done": False,
        },
        {
            "step": 5,
            "title": "Vote!",
            "description": "Go to your polling location and vote.",
            "action": "Polls open 6 AM – 8 PM on Election Day.",
            "done": False,
        },
    ]


def _returning_steps() -> List[Dict[str, Any]]:
    """Quick checklist for experienced returning voters.

    Returns:
        List[Dict[str, Any]]: A list of checklist steps.
    """
    return [
        {
            "step": 1,
            "title": "Verify Registration",
            "description": "Quick check — confirm you are still registered.",
            "action": "Visit vote.org/am-i-registered-to-vote/",
            "done": False,
        },
        {
            "step": 2,
            "title": "Find Polling Location",
            "description": "Polling locations can change between elections.",
            "action": "Check the Election Info panel.",
            "done": False,
        },
        {
            "step": 3,
            "title": "Bring Your ID & Vote",
            "description": "Show up with your ID and cast your ballot.",
            "action": "Polls open 6 AM – 8 PM.",
            "done": False,
        },
    ]
