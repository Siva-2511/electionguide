"""
services/world_elections.py
Basic election info for UK, Australia, Canada.
All returns build_response() schema. Zero network calls — static structured data.
"""

from typing import Dict, Any
from utils.response import build_response
from utils.response_guard import enforce_schema

WORLD_DATA = {
    "uk": {
        "country": "United Kingdom",
        "election_name": "UK General Election 2024",
        "conducted_by": "The Electoral Commission",
        "official_website": "https://www.electoralcommission.org.uk",
        "voter_portal": "https://www.gov.uk/register-to-vote",
        "election_day": "July 4, 2024",
        "result": "Labour Party won majority",
        "next_election": {"type": "UK General Election", "expected_year": "2029"},
        "voting_system": "First Past The Post (FPTP)",
        "voting_age": 18,
        "total_seats": 650,
        "registration": {
            "portal": "https://www.gov.uk/register-to-vote",
            "deadline": "12 working days before election",
            "online": True,
        },
        "id_required": "Photo ID required since 2023 (passport, driving licence, etc.)",
        "voting_hours": "7:00 AM – 10:00 PM",
        "useful_links": {
            "register": "https://www.gov.uk/register-to-vote",
            "find_polling_station": "https://www.gov.uk/find-polling-station",
            "electoral_commission": "https://www.electoralcommission.org.uk",
        },
        "source": "electoral_commission_mock",
        "note": "Based on UK Electoral Commission 2024 data. Visit electoralcommission.org.uk for latest info.",
    },
    "australia": {
        "country": "Australia",
        "election_name": "Australian Federal Election 2025",
        "conducted_by": "Australian Electoral Commission (AEC)",
        "official_website": "https://www.aec.gov.au",
        "voter_portal": "https://www.aec.gov.au/Enrolment/",
        "election_day": "May 3, 2025",
        "voting_system": "Preferential voting (House) + Single Transferable Vote (Senate)",
        "voting_compulsory": True,
        "voting_age": 18,
        "total_seats": 151,
        "registration": {
            "portal": "https://www.aec.gov.au/Enrolment/",
            "note": "Automatic enrolment for citizens 18+",
        },
        "id_required": "No photo ID required — enrolled voters confirmed by name/address",
        "voting_hours": "8:00 AM – 6:00 PM",
        "fine_for_not_voting": "AUD $20 (voting is compulsory)",
        "next_election": {
            "type": "Australian Federal Election",
            "expected_year": "2028",
        },
        "useful_links": {
            "enrol": "https://www.aec.gov.au/Enrolment/",
            "find_polling_place": "https://www.aec.gov.au/election/pollingplaces.htm",
            "aec_website": "https://www.aec.gov.au",
        },
        "source": "aec_mock",
        "note": "Based on AEC 2025 data. Visit aec.gov.au for latest info.",
    },
    "canada": {
        "country": "Canada",
        "election_name": "Canadian Federal Election 2025",
        "conducted_by": "Elections Canada",
        "official_website": "https://www.elections.ca",
        "voter_portal": "https://ereg.elections.ca",
        "election_day": "April 28, 2025",
        "voting_system": "First Past The Post (FPTP)",
        "voting_age": 18,
        "total_seats": 343,
        "registration": {
            "portal": "https://ereg.elections.ca",
            "note": "Can register at polling station on election day",
        },
        "id_required": "One piece of ID with name and address, OR two pieces with name",
        "voting_hours": "9:30 AM – 9:30 PM local time",
        "next_election": {"type": "Canadian Federal Election", "expected_year": "2029"},
        "useful_links": {
            "register": "https://ereg.elections.ca",
            "find_polling_place": "https://www.elections.ca/content.aspx?section=vot&dir=bkg&document=index&lang=e",
            "elections_canada": "https://www.elections.ca",
        },
        "source": "elections_canada_mock",
        "note": "Based on Elections Canada 2025 data. Visit elections.ca for latest info.",
    },
}


@enforce_schema
def get_world_election_info(country_code: str) -> Dict[str, Any]:
    """Returns election info for UK, Australia, or Canada.

    Pure static data — zero network calls, zero AI.

    Args:
        country_code (str): The country code (uk, australia, canada).

    Returns:
        Dict[str, Any]: build_response() schema with election data.
    """
    code = country_code.lower().strip()
    if code not in WORLD_DATA:
        return build_response(
            success=False,
            error=f"Country '{country_code}' not supported. Available: uk, australia, canada",
        )
    return build_response(success=True, data=WORLD_DATA[code])
