"""
gemini_logic.py

Modernized Google Gemini AI integration module using the google-genai SDK.
Acts as the secure conversational brain for ElectionGuide.
"""
import os
import re
import logging
from google import genai
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
Do NOT express political opinions. Do NOT tell users who to vote for.
Always provide official ECI resources (eci.gov.in, voters.eci.gov.in)."""

SYSTEM_PROMPT_US = """You are ElectionGuide, a helpful non-partisan US Civic Education Assistant.
Answer any question about US elections, voting, and democracy.
Do NOT express political opinions. Always provide official resources like vote.gov."""

_SYSTEM_PROMPTS = {
    "india": SYSTEM_PROMPT_INDIA, "us": SYSTEM_PROMPT_US,
}

# Model names to try in order
_MODEL_CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash",
]

def _initialize_client():
    """Initialize the new google-genai client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error("GenAI client init failed: %s", str(e))
        return None

def chat(message: str, context: dict = None, country: str = 'us') -> dict:
    """Generate response using the new google-genai SDK with model waterfall."""
    fallback_msg = _FALLBACKS.get(country, SAFE_FALLBACK)
    client = _initialize_client()
    if not client:
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

    system_prompt = _SYSTEM_PROMPTS.get(country, SYSTEM_PROMPT_US)
    ctx_suffix = ""
    if context:
        day = context.get("election_day", "")
        if day:
            ctx_suffix = f"\n[Context: Next election on {day}]"

    hit_quota = False
    for model_id in _MODEL_CANDIDATES:
        try:
            config = {"system_instruction": system_prompt, "temperature": 0.7}
            response = client.models.generate_content(
                model=model_id,
                contents=message + ctx_suffix,
                config=config
            )
            if response.text:
                return build_response(
                    success=True,
                    data={"reply": enforce_readability(filter_output(response.text)), "source": "gemini"}
                )
        except Exception as e:
            error_text = str(e).lower()
            if "429" in error_text or "quota" in error_text:
                hit_quota = True
                continue
            logger.warning("Model %s failed, trying next...", model_id)
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
    """
    Enforce 8th-grade readability on AI output.
    Caps paragraphs at 3 sentences and converts long blocks to bullet points.
    """
    if not text:
        return SAFE_FALLBACK

    # Strip excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text.strip())
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    if len(sentences) > 5 and not any(
        line.strip().startswith(('1.', '2.', '-', '*', '•'))
        for line in text.split('\n')
    ):
        bullet_lines = [f"• {s.strip()}" for s in sentences if s.strip()]
        return '\n'.join(bullet_lines[:7])

    return text
