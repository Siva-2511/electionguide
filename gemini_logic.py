"""
gemini_logic.py

Restored to stable google-generativeai SDK for hackathon submission stability.
Includes high-performance caching and anti-throttling logic.
"""
import os
import re
import logging
import time
import google.generativeai as genai
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

# Hardened system prompts
SYSTEM_PROMPT_INDIA = """You are ElectionGuide, a helpful non-partisan India Election Education Assistant.
Answer any question about Indian elections, voting, civic processes, and democracy.
Do NOT express political opinions. Always provide official ECI resources (eci.gov.in, voters.eci.gov.in)."""

SYSTEM_PROMPT_US = """You are ElectionGuide, a helpful non-partisan US Civic Education Assistant.
Answer any question about US elections, voting, and democracy.
Do NOT express political opinions. Always provide official resources like vote.gov."""

_SYSTEM_PROMPTS = {
    "india": SYSTEM_PROMPT_INDIA, "us": SYSTEM_PROMPT_US,
}

# Stable model names for the proven SDK
_MODEL_CANDIDATES = [
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
]

_response_cache = {}  # Global in-memory cache

def chat(message: str, context: dict = None, country: str = 'us') -> dict:
    """Generate response using the stable SDK with model waterfall and caching."""
    fallback_msg = _FALLBACKS.get(country, SAFE_FALLBACK)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

    # Check cache first
    cache_key = f"{country}:{message.strip().lower()[:50]}"
    if cache_key in _response_cache:
        return _response_cache[cache_key]

    system_prompt = _SYSTEM_PROMPTS.get(country, SYSTEM_PROMPT_US)
    ctx_suffix = ""
    if context:
        day = context.get("election_day", "")
        if day:
            ctx_suffix = f"\n[Context: Next election on {day}]"

    try:
        genai.configure(api_key=api_key)
    except Exception:
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

    hit_quota = False
    for model_name in _MODEL_CANDIDATES:
        try:
            # Robust initialization for different SDK versions
            try:
                model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                enriched_msg = message + ctx_suffix
            except (TypeError, Exception):
                # Fallback for older SDKs that don't support system_instruction argument
                model = genai.GenerativeModel(model_name=model_name)
                enriched_msg = f"{system_prompt}\n\nUser Question: {message}{ctx_suffix}"

            response = model.generate_content(enriched_msg)
            
            if response.text:
                result = build_response(
                    success=True,
                    data={"reply": enforce_readability(filter_output(response.text)), "source": "gemini"}
                )
                _response_cache[cache_key] = result
                return result
        except Exception as e:
            error_text = str(e).lower()
            logger.error("Model %s crashed: %s", model_name, str(e)) # LOG THE EXACT ERROR
            if "429" in error_text or "quota" in error_text:
                hit_quota = True
                time.sleep(1) 
                continue
            continue

    if hit_quota:
        return build_response(success=True, data={"reply": INDIA_FALLBACK if country == 'india' else SAFE_FALLBACK, "source": "quota_exceeded"})
    
    return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

def detect_intent(message: str) -> dict:
    """Keyword-based intent detection."""
    msg = message.lower()
    if any(k in msg for k in ["register", "registration", "sign up", "form 6"]):
        return {"intent": "voter_registration", "confidence": "high"}
    if any(k in msg for k in ["eligib", "can i vote", "old enough", "age"]):
        return {"intent": "eligibility", "confidence": "high"}
    if any(k in msg for k in ["checklist", "steps", "how do i", "prepare"]):
        return {"intent": "voter_checklist", "confidence": "high"}
    return {"intent": "general", "confidence": "low"}

def filter_output(text: str) -> str:
    """Basic filter for biased content."""
    forbidden = [r"\bvote for\b", r"\byou should vote for\b", r"\bbest choice\b"]
    for pattern in forbidden:
        if re.search(pattern, text, re.IGNORECASE):
            return SAFE_FALLBACK
    return text

def enforce_readability(text: str) -> str:
    """Bullet-point formatter for readability."""
    if not text: return SAFE_FALLBACK
    text = re.sub(r'[ \t]+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 5:
        bullet_lines = [f"• {s.strip()}" for s in sentences if s.strip()]
        return '\n'.join(bullet_lines[:7])
    return text
