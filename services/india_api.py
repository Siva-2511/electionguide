"""
services/india_api.py
India Election Commission data service — updated for 2026.
Returns build_response() schema always. Zero AI calls.
"""

import logging
import requests
from typing import Dict, Any, Optional
from utils.response import build_response
from utils.response_guard import enforce_schema

logger = logging.getLogger(__name__)

# India data — Tamil Nadu Vidhan Sabha 2026 (primary) + Lok Sabha 2024 (reference)
INDIA_MOCK_DATA = {
    "country": "India",
    "election_name": "Tamil Nadu Vidhan Sabha Election 2026",
    "election_type": "State Legislative Assembly (Vidhan Sabha)",
    "conducted_by": "Election Commission of India (ECI)",
    "eci_website": "https://www.eci.gov.in",
    "results_portal": "https://results.eci.gov.in",
    "voter_portal": "https://voters.eci.gov.in",
    "election_day": "April 23, 2026",
    "result_date": "May 4, 2026",
    "election_label": "Tamil Nadu Legislative Assembly Election",
    "election_note_cm": "Voters elect 234 MLAs. The majority party/alliance forms government and selects the Chief Minister.",
    "pm_election_future": {
        "label": "Next PM Election (Lok Sabha 2029)",
        "expected": "2029",
        "note": "The next General Election to choose India's Prime Minister is expected in 2029. Every registered Indian citizen 18+ can vote.",
        "quote": '"The ballot is stronger than the bullet." — Abraham Lincoln',
    },
    "total_seats": 234,
    "total_voters": "62.3 Million (6.23 crore in TN)",
    "voting_method": "Electronic Voting Machine (EVM) with VVPAT",
    "voting_hours": "7:00 AM – 6:00 PM (may vary by constituency)",
    # Tamil Nadu 2026 major parties (10 major parties contesting)
    "tn_parties_2026": [
        {
            "name": "DMK",
            "full": "Dravida Munnetra Kazhagam",
            "alliance": "INDIA Alliance",
        },
        {
            "name": "AIADMK",
            "full": "All India Anna Dravida Munnetra Kazhagam",
            "alliance": "Independent",
        },
        {"name": "BJP", "full": "Bharatiya Janata Party", "alliance": "NDA"},
        {
            "name": "INC",
            "full": "Indian National Congress",
            "alliance": "INDIA Alliance",
        },
        {
            "name": "VCK",
            "full": "Viduthalai Chiruthaigal Katchi",
            "alliance": "INDIA Alliance",
        },
        {"name": "PMK", "full": "Pattali Makkal Katchi", "alliance": "NDA"},
        {
            "name": "MDMK",
            "full": "Marumalarchi Dravida Munnetra Kazhagam",
            "alliance": "INDIA Alliance",
        },
        {
            "name": "TVK",
            "full": "Tamilaga Vettri Kazhagam (Vijay Party)",
            "alliance": "INDIA Alliance",
        },
        {"name": "DMDK", "full": "Desiya Murpokku Dravida Kazhagam", "alliance": "NDA"},
        {
            "name": "CPI(M)",
            "full": "Communist Party of India (Marxist)",
            "alliance": "INDIA Alliance",
        },
    ],
    # Tamil Nadu Vidhan Sabha 2026 — single-phase state election
    "election_phases": [
        {
            "phase": "Single Phase",
            "date": "April 23, 2026",
            "states": "Entire Tamil Nadu (234 constituencies)",
        },
    ],
    "registration_info": {
        "portal": "https://voters.eci.gov.in",
        "form": "Form 6 for new voters",
        "min_age": 18,
        "id_required": "Aadhaar, EPIC (Voter ID), Passport, or 11 other valid IDs",
    },
    "id_types_accepted": [
        "Elector Photo Identity Card (EPIC / Voter ID)",
        "Aadhaar Card",
        "Passport",
        "Driving Licence",
        "PAN Card",
        "NPR Smart Card",
        "MNREGA Job Card",
        "Pension Documents with photo",
        "Service Identity Card (Govt employees)",
        "Health Insurance Smart Card",
        "Passbook with photo (Banks/Post Office)",
        "Student ID with photo",
    ],
    "next_election": {
        "type": "19th Lok Sabha General Election",
        "expected_year": "2029",
        "note": "Every 5 years as per Constitution of India",
    },
    "useful_links": {
        "voter_registration": "https://voters.eci.gov.in",
        "voter_list_search": "https://electoralsearch.eci.gov.in",
        "candidate_info": "https://affidavit.eci.gov.in",
        "results": "https://results.eci.gov.in",
        "complaints": "https://cvigil.eci.gov.in",
    },
    "source": "eci_mock_data",
    "note": "Tamil Nadu Vidhan Sabha 2026 data. Results expected May 4, 2026. Visit eci.gov.in for latest.",
}


@enforce_schema
def get_india_election_info(state: Optional[str] = None) -> Dict[str, Any]:
    """Fetch India election information with ECI connectivity check.

    Falls back to structured 2026 mock data.

    Args:
        state (Optional[str]): The specific state to query. Defaults to None.

    Returns:
        Dict[str, Any]: build_response() schema with election data.
    """
    try:
        resp = requests.get("https://www.eci.gov.in", timeout=3)
        if resp.status_code == 200:
            logger.info("ECI website reachable — returning structured data")
    except Exception:
        logger.info("ECI website not reachable — using mock data")

    data = dict(INDIA_MOCK_DATA)
    if state:
        data["queried_state"] = state
        data["state_note"] = (
            f"For {state}-specific schedule, visit https://www.eci.gov.in "
            "or your state's Chief Electoral Officer website."
        )
    return build_response(success=True, data=data)


def get_india_eligibility_info() -> Dict[str, Any]:
    """Return India-specific eligibility rules.

    Returns:
        Dict[str, Any]: build_response() schema with eligibility rules.
    """
    return build_response(
        success=True,
        data={
            "country": "India",
            "min_age": 18,
            "citizenship": "Must be a citizen of India",
            "registration": "Must be registered on the Electoral Roll of your constituency",
            "register_at": "https://voters.eci.gov.in (Form 6)",
            "id_required": "EPIC (Voter ID) or any of 12 approved photo IDs",
            "disqualifications": [
                "Non-citizen of India",
                "Under 18 years of age",
                "Unsound mind (declared by court)",
                "Corrupt practices or election offences",
                "Serving sentence of 2+ years imprisonment",
            ],
        },
    )
