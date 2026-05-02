"""
gemini_logic.py

Production-Grade Gemini integration for ElectionGuide.
Focus: Stability, Safety, Deterministic Execution, and Hard Fail Protection.
"""

import os
import re
import logging
import hashlib
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from google import genai
from google.genai import types
from utils.response import build_response

logger = logging.getLogger(__name__)

# -----------------------
# HARD GUARANTEE SETTINGS
# -----------------------
CACHE_VERSION = "v1"
_CACHE_MAX = 500
_GEMINI_TIMEOUT = 8  # HARD ENFORCED

_executor = ThreadPoolExecutor(max_workers=4)

# -----------------------
# Fallbacks
# -----------------------
SAFE_FALLBACK = (
    "I'm your US Election Guide. I can help with voter registration, eligibility, "
    "voting steps, and election dates. What would you like to know?"
)

INDIA_FALLBACK = (
    "Namaste! I'm your India Election Guide. I can help with voter registration, "
    "eligibility (18+), EVM voting steps, and election schedules. "
    "What would you like to know? / आप क्या जानना चाहते हैं?"
)

FALLBACKS = {
    "india": INDIA_FALLBACK,
    "us": SAFE_FALLBACK,
}

# -----------------------
# System Prompts
# -----------------------
SYSTEM_PROMPTS = {
    "india": "Non-partisan India election assistant. Use only ECI sources (eci.gov.in).",
    "us": "Non-partisan US election assistant. Use vote.gov only.",
}

# -----------------------
# Cache (Thread-safe LRU)
# -----------------------
_cache = OrderedDict()
_lock = threading.Lock()

# -----------------------
# Client
# -----------------------
def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

# -----------------------
# Model selection (stable only)
# -----------------------
PREFERRED_MODELS = [
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
]

def _pick_model(client):
    try:
        models = client.models.list() or []

        for pref in PREFERRED_MODELS:
            for m in models:
                name = m.name.replace("models/", "")
                if pref in name and "preview" not in name.lower():
                    return name

        for m in models:
            name = m.name.replace("models/", "")
            if "flash" in name.lower() and "preview" not in name.lower():
                return name

    except Exception as e:
        logger.warning("Model discovery failed: %s", e)

    return PREFERRED_MODELS[0]

# -----------------------
# Response extraction
# -----------------------
def _extract_text(resp):
    try:
        if getattr(resp, "text", None):
            return resp.text

        candidates = getattr(resp, "candidates", None)
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None)
            if parts:
                return getattr(parts[0], "text", "")
    except Exception:
        pass
    return ""

# -----------------------
# Safety filter (strict but safe)
# -----------------------
def filter_output(text: str, country: str = "us"):
    if not text:
        return ""

    blocked_patterns = [
        r"\bvote for\b",
        r"\byou should vote for\b",
        r"\bbest candidate\b",
        r"\bbest choice\b",
        r"\bsupport the\b",
        r"\bshould choose\b",
        r"\bwinner is\b",
    ]

    for p in blocked_patterns:
        if re.search(p, text, re.IGNORECASE):
            return FALLBACKS.get(country, SAFE_FALLBACK)

    return text

# -----------------------
# Formatting
# -----------------------
def enforce_readability(text: str):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)

    if len(sentences) > 5:
        return "\n".join(
            f"• {s.strip()}" for s in sentences[:7] if s.strip()
        )

    return text

# -----------------------
# CORE GEMINI EXECUTION (with HARD TIMEOUT)
# -----------------------
def _call_gemini(client, model, prompt, system_instruction):
    def task():
        return client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=700,
            ),
        )

    future = _executor.submit(task)

    try:
        return future.result(timeout=_GEMINI_TIMEOUT)
    except TimeoutError:
        future.cancel()
        raise TimeoutError("Gemini request timed out")

# -----------------------
# MAIN CHAT
# -----------------------
def chat(message: str, context=None, country="us"):
    start_time = time.time()

    raw = (message or "").strip()
    country = (country or "us").lower()

    if country not in FALLBACKS:
        country = "us"

    fallback = FALLBACKS[country]

    if not raw:
        return build_response(True, {"reply": fallback, "source": "fallback"})

    normalized = " ".join(raw.lower().split())
    ctx_id = context.get("election_day") if context else ""

    cache_key = hashlib.md5(
        f"{CACHE_VERSION}:{country}:{normalized}:{ctx_id}".encode()
    ).hexdigest()

    # ---------------- CACHE READ ----------------
    with _lock:
        if cache_key in _cache:
            _cache.move_to_end(cache_key)
            return build_response(True, _cache[cache_key])

    client = _get_client()
    if not client:
        return build_response(True, {"reply": fallback, "source": "fallback"})

    model = _pick_model(client)

    prompt = raw
    if context and context.get("election_day"):
        prompt += f"\nElection date: {context['election_day']}"

    try:
        resp = _call_gemini(
            client,
            model,
            prompt,
            SYSTEM_PROMPTS[country]
        )

        text = _extract_text(resp)

        if not text:
            return build_response(True, {"reply": fallback, "source": "fallback"})

        filtered = filter_output(text, country)
        cleaned = enforce_readability(filtered)

        result = {"reply": cleaned, "source": "gemini"}

        # ---------------- CACHE WRITE ----------------
        with _lock:
            _cache[cache_key] = result
            _cache.move_to_end(cache_key)

            if len(_cache) > _CACHE_MAX:
                _cache.popitem(last=False)

        logger.info("Response time: %.2fs", time.time() - start_time)

        return build_response(True, result)

    except Exception as e:
        logger.error("Gemini error: %s", str(e))
        return build_response(True, {"reply": fallback, "source": "fallback"})


# -----------------------
# INTENT DETECTION
# -----------------------
def detect_intent(message: str) -> dict:
    msg = (message or "").lower()

    if "register" in msg:
        return {"intent": "voter_registration", "confidence": "high"}

    if "how" in msg or "steps" in msg:
        return {"intent": "voter_checklist", "confidence": "medium"}

    if "vote" in msg or "eligible" in msg:
        return {"intent": "eligibility", "confidence": "high"}

    return {"intent": "general", "confidence": "low"}
