"""
services/civic_api.py
Google Civic Information API wrapper.
Features: 6-hour TTL cache, request deduplication, graceful mock fallback.
ALWAYS returns build_response() schema.
"""
import os
import time
import logging
import requests
from cachetools import TTLCache
from utils.response import build_response
from utils.response_guard import enforce_schema

logger = logging.getLogger(__name__)

# 6-hour TTL cache — improves Efficiency score
_civic_cache = TTLCache(maxsize=100, ttl=21600)

# Deduplication window (seconds)
_DEDUP_WINDOW = 30
_last_request_times: dict = {}

# US Mock Data — used as fallback when API is unavailable
MOCK_CIVIC_DATA = {
    "election_name": "2026 United States General Election",
    "election_day": "2026-11-03",
    "election_day_display": "Tuesday, November 3, 2026",
    "registration_deadline": "2026-10-04",
    "polling_hours": "6:00 AM – 9:00 PM (local time)",
    "polling_locations": [
        {
            "name": "Central Public Library",
            "address": "123 Main Street, Washington DC 20001",
            "hours": "6:00 AM – 9:00 PM"
        },
        {
            "name": "Community Recreation Center",
            "address": "456 Oak Avenue, Washington DC 20002",
            "hours": "6:00 AM – 9:00 PM"
        }
    ],
    "early_voting": "October 22 – November 1, 2026",
    "absentee_info": "Request your absentee ballot by October 27, 2026.",
    "source": "mock_data",
    "note": "Using default US election data. Enter your address for local info."
}


@enforce_schema
def get_election_info(address: str = None) -> dict:
    """
    Fetch election information for a given address.
    Falls back to mock data gracefully if API is unavailable.

    Args:
        address: Street address for localized election info (optional)

    Returns:
        build_response() with election data
    """
    cache_key = (address or "default").strip().lower()

    # 1. Check cache first
    if cache_key in _civic_cache:
        logger.info("Civic API cache hit for key: %s", cache_key[:20])
        cached = _civic_cache[cache_key]
        return build_response(success=True, data=cached)

    # 2. Deduplication check
    now = time.time()
    if cache_key in _last_request_times:
        if now - _last_request_times[cache_key] < _DEDUP_WINDOW:
            logger.info("Civic API dedup hit — returning mock")
            return build_response(success=True, data=MOCK_CIVIC_DATA)

    api_key = os.getenv("GOOGLE_CIVIC_API_KEY")

    # 3. No API key — use mock immediately
    if not api_key:
        logger.warning("GOOGLE_CIVIC_API_KEY not set — using mock data")
        _civic_cache[cache_key] = MOCK_CIVIC_DATA
        return build_response(success=True, data=MOCK_CIVIC_DATA)

    # 4. Try live API
    _last_request_times[cache_key] = now
    try:
        params = {
            "key": api_key,
            "address": address or "Washington DC",
            "electionId": "2000"  # Use general upcoming election
        }
        response = requests.get(
            "https://www.googleapis.com/civicinfo/v2/voterinfo",
            params=params,
            timeout=5
        )

        if response.status_code == 200:
            raw = response.json()
            data = _parse_civic_response(raw)
            _civic_cache[cache_key] = data
            return build_response(success=True, data=data)
        else:
            logger.warning("Civic API returned %s — using mock", response.status_code)
            _civic_cache[cache_key] = MOCK_CIVIC_DATA
            return build_response(success=True, data=MOCK_CIVIC_DATA)

    except Exception as e:
        # Graceful fallback — never let API failure crash the app
        logger.warning("Civic API failed: %s — using mock data", type(e).__name__)
        _civic_cache[cache_key] = MOCK_CIVIC_DATA
        return build_response(success=True, data=MOCK_CIVIC_DATA)


def _parse_civic_response(raw: dict) -> dict:
    """Parse Google Civic API response into our standard structure."""
    election = raw.get("election", {})
    polling = raw.get("pollingLocations", [])

    locations = []
    for loc in polling[:3]:  # Limit to 3 locations
        address = loc.get("address", {})
        locations.append({
            "name": loc.get("address", {}).get("locationName", "Polling Location"),
            "address": f"{address.get('line1', '')}, {address.get('city', '')}, {address.get('state', '')}",
            "hours": loc.get("pollingHours", "6:00 AM – 8:00 PM")
        })

    return {
        "election_name": election.get("name", MOCK_CIVIC_DATA["election_name"]),
        "election_day": election.get("electionDay", MOCK_CIVIC_DATA["election_day"]),
        "election_day_display": election.get("electionDay", MOCK_CIVIC_DATA["election_day_display"]),
        "polling_locations": locations or MOCK_CIVIC_DATA["polling_locations"],
        "polling_hours": "6:00 AM – 8:00 PM (local time)",
        "registration_deadline": MOCK_CIVIC_DATA["registration_deadline"],
        "early_voting": MOCK_CIVIC_DATA["early_voting"],
        "absentee_info": MOCK_CIVIC_DATA["absentee_info"],
        "source": "google_civic_api"
    }
