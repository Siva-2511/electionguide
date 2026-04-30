"""
services/eligibility.py
Pure deterministic voting eligibility logic — supports India, US, UK, Australia, Canada.
ZERO AI calls. ZERO network calls. Always returns build_response() schema.
"""
from utils.response import build_response
from utils.response_guard import enforce_schema

MIN_VOTING_AGE = 18

# Country-specific text config
COUNTRY_CONFIG = {
    "india": {
        "citizenship_label": "Indian citizen",
        "not_citizen_reason": "You must be a citizen of India to vote.",
        "not_citizen_step": "Visit eci.gov.in for voter eligibility information.",
        "register_url": "voters.eci.gov.in",
        "eligible_step": "Register at voters.eci.gov.in (Form 6) and find your polling booth.",
        "first_time_step": "Register at voters.eci.gov.in using Form 6. It only takes a few minutes!",
        "preregister_note": None,  # India has no pre-registration for under-18
    },
    "us": {
        "citizenship_label": "US citizen",
        "not_citizen_reason": "You must be a US citizen to vote in federal elections.",
        "not_citizen_step": "Learn about naturalization at uscis.gov.",
        "register_url": "vote.gov",
        "eligible_step": "Check your registration status at vote.gov and find your polling location.",
        "first_time_step": "Register to vote at vote.gov — it only takes 2 minutes!",
        "preregister_note": "Many US states allow 17-year-olds to pre-register. You can register now and vote at 18!",
    },
    "uk": {
        "citizenship_label": "UK citizen",
        "not_citizen_reason": "You must be a UK, Irish, or qualifying Commonwealth citizen to vote.",
        "not_citizen_step": "Visit gov.uk/register-to-vote for eligibility details.",
        "register_url": "gov.uk/register-to-vote",
        "eligible_step": "Register at gov.uk/register-to-vote and find your polling station.",
        "first_time_step": "Register at gov.uk/register-to-vote — quick and easy!",
        "preregister_note": "You can register to vote from age 16 in the UK but can only vote at 18.",
    },
    "australia": {
        "citizenship_label": "Australian citizen",
        "not_citizen_reason": "You must be an Australian citizen to vote in federal elections.",
        "not_citizen_step": "Visit aec.gov.au for enrolment eligibility.",
        "register_url": "aec.gov.au/Enrolment",
        "eligible_step": "Enrol at aec.gov.au. Note: voting is compulsory in Australia!",
        "first_time_step": "Enrol at aec.gov.au — remember, voting is compulsory in Australia!",
        "preregister_note": "You can enrol at 17 but can only vote at 18 in Australia.",
    },
    "canada": {
        "citizenship_label": "Canadian citizen",
        "not_citizen_reason": "You must be a Canadian citizen to vote in federal elections.",
        "not_citizen_step": "Visit elections.ca for voter eligibility information.",
        "register_url": "elections.ca",
        "eligible_step": "Register at elections.ca or at your polling station on election day.",
        "first_time_step": "Register at elections.ca — you can even register on election day!",
        "preregister_note": None,
    },
}


def _get_config(country: str) -> dict:
    return COUNTRY_CONFIG.get(country.lower(), COUNTRY_CONFIG["us"])


@enforce_schema
def check(age, citizen: bool = True, country: str = "us") -> dict:
    """
    Determine voting eligibility based on age, citizenship, and country.
    Pure deterministic — no AI, no network calls.
    """
    cfg = _get_config(country)
    validated_age = _parse_age(age)

    if validated_age is None:
        return build_response(
            success=False,
            error="Invalid age. Please provide a number between 0 and 120."
        )

    # Non-citizen check
    if not citizen:
        return build_response(
            success=True,
            data={
                "eligible": False,
                "reason": cfg["not_citizen_reason"],
                "next_step": cfg["not_citizen_step"],
                "age_checked": validated_age,
                "country": country,
            }
        )

    # Under 17 (too young even to pre-register in most countries)
    if validated_age < 17:
        return build_response(
            success=True,
            data={
                "eligible": False,
                "reason": f"You are {validated_age}. The minimum voting age is {MIN_VOTING_AGE}.",
                "next_step": "Keep learning about elections — every future voter matters!",
                "age_checked": validated_age,
                "country": country,
            }
        )

    # Age 17 (special case — pre-registration in some countries)
    if validated_age == 17:
        note = cfg.get("preregister_note") or f"You must be {MIN_VOTING_AGE} to vote."
        return build_response(
            success=True,
            data={
                "eligible": False,
                "reason": f"You are {validated_age}. You must be {MIN_VOTING_AGE} to vote.",
                "next_step": note,
                "age_checked": validated_age,
                "can_preregister": bool(cfg.get("preregister_note")),
                "country": country,
            }
        )

    # Exactly 18 — first-time voter
    if validated_age == MIN_VOTING_AGE:
        return build_response(
            success=True,
            data={
                "eligible": True,
                "reason": f"You are {validated_age} — eligible to vote for the first time!",
                "next_step": cfg["first_time_step"],
                "age_checked": validated_age,
                "first_time_voter": True,
                "country": country,
            }
        )

    # Standard eligible adult
    return build_response(
        success=True,
        data={
            "eligible": True,
            "reason": f"You are {validated_age} and a {cfg['citizenship_label']} — eligible to vote.",
            "next_step": cfg["eligible_step"],
            "age_checked": validated_age,
            "first_time_voter": False,
            "country": country,
        }
    )


def _parse_age(age) -> int | None:
    """Safely parse age to integer. Returns None for invalid inputs."""
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 120:
            return None
        return age_int
    except (ValueError, TypeError):
        return None
