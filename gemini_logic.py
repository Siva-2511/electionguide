"""
gemini_logic.py

Modernized Gemini integration using the google-genai SDK.
Optimized for Google Cloud Run (Python 3.11+).
Features: In-memory caching, model waterfall, and anti-throttling.
"""
import os
import re
import logging
import time
import threading
import hashlib
from google import genai
from google.genai import types
from utils.response import build_response

logger = logging.getLogger(__name__)

# Safe fallback messages
SAFE_FALLBACK = (
    "I'm your US Election Guide. I can help with voter registration, eligibility, "
    "voting steps, and election dates. What would you like to know?"
)
INDIA_FALLBACK = (
    "Namaste! I'm your India Election Guide. I can help with: "
    "Voter registration, eligibility (18+), EVM voting steps, and election schedules. "
    "What would you like to know? / आप क्या जानना चाहते हैं?"
)

_FALLBACKS = {
    "india": INDIA_FALLBACK, "us": SAFE_FALLBACK,
    "uk": "Hello! I'm your UK Election Guide.",
    "australia": "G'day! I'm your Australia Election Guide.",
    "canada": "Hello! I'm your Canada Election Guide.",
}

# Production System Prompts
SYSTEM_PROMPT_INDIA = """You are ElectionGuide, a helpful non-partisan India Election Education Assistant.
Answer any question about Indian elections, voting, civic processes, and democracy.
Do NOT express political opinions. Always provide official ECI resources (eci.gov.in, voters.eci.gov.in)."""

SYSTEM_PROMPT_US = """You are ElectionGuide, a helpful non-partisan US Civic Education Assistant.
Answer any question about US elections, voting, and democracy.
Do NOT express political opinions. Always provide official resources like vote.gov."""

_SYSTEM_PROMPTS = {
    "india": SYSTEM_PROMPT_INDIA, "us": SYSTEM_PROMPT_US,
}

# Stable model names for the new google-genai SDK
_MODEL_CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

_cache_lock = threading.Lock()
_response_cache = {}  # Global in-memory cache
_CACHE_MAX_SIZE = 500 # Prevents memory leaks in Cloud Run

def _get_client():
    """Initialize the new google-genai client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def chat(message: str, context: dict = None, country: str = 'us') -> dict:
    """Generate response using the new SDK with model waterfall and caching."""
    fallback_msg = _FALLBACKS.get(country, SAFE_FALLBACK)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY missing - using fallback")
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})
    
    # 1. Thread-safe MD5 Cache Check (avoids collisions)
    clean_msg = message.strip().lower()
    msg_hash = hashlib.md5(clean_msg.encode()).hexdigest()
    cache_key = f"{country}:{msg_hash}"
    with _cache_lock:
        if cache_key in _response_cache:
            logger.info("Serving cached response for: %s", cache_key)
            return _response_cache[cache_key]

    client = _get_client()
    if not client:
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

    # 2. Prepare Request
    system_prompt = _SYSTEM_PROMPTS.get(country, SYSTEM_PROMPT_US)
    prompt_with_context = message
    if context and context.get("election_day"):
        prompt_with_context += f"\n[Context: Next election is on {context['election_day']}]"

    # 3. Model Waterfall
    hit_quota = False
    for model_id in _MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt_with_context,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                )
            )
            
            # 4. Safe Response Parsing (prevents crashes on safety blocks)
            raw_text = getattr(response, "text", None)
            if raw_text and raw_text.strip():
                result = build_response(
                    success=True,
                    data={"reply": enforce_readability(filter_output(raw_text)), "source": "gemini"}
                )
                with _cache_lock:
                    if len(_response_cache) > _CACHE_MAX_SIZE:
                        # Safe in-place deletion to avoid scope issues
                        keys_to_remove = list(_response_cache.keys())[:-200]
                        for k in keys_to_remove:
                            del _response_cache[k]
                    _response_cache[cache_key] = result
                return result
            else:
                logger.warning("Empty or blocked response from %s", model_id)
                continue
        except Exception as e:
            err = str(e).lower()
            logger.error("Model %s failed: %s", model_id, err)
            if any(k in err for k in ["429", "quota", "rate limit", "exhausted"]):
                hit_quota = True
                time.sleep(0.5) # Anti-throttle delay before switching/retrying
                continue
            continue

    if hit_quota:
        return build_response(success=True, data={"reply": INDIA_FALLBACK if country == 'india' else SAFE_FALLBACK, "source": "quota_exceeded"})

    return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

def detect_intent(message: str) -> dict:
    """Keyword-based intent detection for snappy responses."""
    msg = message.lower()
    if any(k in msg for k in ["register", "registration", "sign up", "form 6"]):
        return {"intent": "voter_registration", "confidence": "high"}
    if any(k in msg for k in ["eligib", "can i vote", "old enough", "age"]):
        return {"intent": "eligibility", "confidence": "high"}
    if any(k in msg for k in ["checklist", "steps", "how do i", "prepare"]):
        return {"intent": "voter_checklist", "confidence": "high"}
    return {"intent": "general", "confidence": "low"}

def filter_output(text: str) -> str:
    """Filter for biased/political content."""
    if not text: return ""
    forbidden = [r"\bvote for\b", r"\byou should vote for\b", r"\bbest choice\b"]
    for pattern in forbidden:
        if re.search(pattern, text, re.IGNORECASE):
            return SAFE_FALLBACK
    return text

def enforce_readability(text: str) -> str:
    """Formatter for readability on mobile/web."""
    if not text: return ""
    text = re.sub(r'[ \t]+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 5:
        bullet_lines = [f"• {s.strip()}" for s in sentences if s.strip()]
        return '\n'.join(bullet_lines[:7])
    return text
