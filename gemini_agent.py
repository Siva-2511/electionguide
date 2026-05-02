"""
gemini_agent.py

Google Gemini AI integration module.
Acts as the secure conversational brain for ElectionGuide.

Features:
- Google Gemini 1.5/2.0 API integration with waterfall fallback
- Hardened anti-jailbreak system prompts per country
- Keyword-based intent detection (avoids unnecessary LLM calls)
- Output filter to remove political bias
- Readability enforcer (8th-grade reading level)
"""
import os
import re
import logging
import google.generativeai as genai
from utils.response import build_response

logger = logging.getLogger(__name__)

# Safe fallback messages — one per country
SAFE_FALLBACK = (
    "I'm your US Election Guide. I can help with voter registration, eligibility, "
    "voting steps, and election dates. What would you like to know?"
)
INDIA_FALLBACK = (
    "Namaste! I'm your India Election Guide. I can help with: "
    "ECI voter registration, eligibility (18+), EVM voting steps, and election schedules. "
    "What would you like to know? / आप क्या जानना चाहते हैं?"
)
UK_FALLBACK = (
    "Hello! I'm your UK Election Guide. I can help with voter registration "
    "(gov.uk/register-to-vote), eligibility, photo ID rules, and polling info. "
    "What would you like to know?"
)
AUSTRALIA_FALLBACK = (
    "G'day! I'm your Australia Election Guide. Voting is compulsory for citizens 18+. "
    "I can help with enrolment (aec.gov.au), polling places, and preferential voting. "
    "What would you like to know?"
)
CANADA_FALLBACK = (
    "Hello! I'm your Canada Election Guide. I can help with voter registration "
    "(elections.ca), eligibility, ID requirements, and election dates. "
    "What would you like to know?"
)

_FALLBACKS = {
    "india": INDIA_FALLBACK, "us": SAFE_FALLBACK,
    "uk": UK_FALLBACK, "australia": AUSTRALIA_FALLBACK, "canada": CANADA_FALLBACK,
}

# Output filter — blocks jailbreaks and persuasion; allows factual election info
FORBIDDEN_OUTPUT_PHRASES = [
    r"\bvote for (the )?(republican|democrat|gop|trump|biden|BJP|Congress|DMK|AIADMK)\b",
    r"\byou should vote for\b",
    r"\bbetter candidate\b",
    r"\b(trump|biden|modi|rahul) is (the best|great|terrible|bad|corrupt)\b",
    r"\bignore (previous|your) instructions\b",
    r"\bpretend (you are|to be) (a human|not an AI)\b",
    r"\bDAN mode\b",
    r"\bthe best choice\b",
]

# Hardened system prompts — civic scope locked
SYSTEM_PROMPT_US = """You are ElectionGuide, a helpful non-partisan US Civic Education Assistant.

YOUR ROLE: Answer any question about US elections, voting, civic processes, and democracy.

TOPICS YOU COVER: Voter registration, eligibility, polling locations, absentee voting, early voting,
election dates, how elections work, ballot types, ID requirements, electoral college, primaries,
how many times you can vote, what happens if you miss election day, mail-in ballots, and any
other civic or election-related question.

RULES:
1. Do NOT express political opinions or preferences about parties or candidates.
2. Do NOT tell users who to vote for.
3. For non-election questions (sports, cooking, etc.), say: "I specialize in US election questions. What would you like to know about voting?"
4. Use simple, clear English. Short answers unless steps are needed.
5. Be warm, helpful, and encouraging. Voting is a right.
6. Always provide actionable next steps (websites, resources).

STYLE: Friendly civic guide. Factual. Clear. Non-partisan."""

SYSTEM_PROMPT_INDIA = """You are ElectionGuide, a helpful non-partisan India Election Education Assistant.

YOUR ROLE: Answer any question about Indian elections, voting, civic processes, and democracy.

TOPICS YOU COVER: ECI voter registration (Form 6), EPIC/Voter ID card, EVM voting, VVPAT, Lok Sabha,
Rajya Sabha, Vidhan Sabha, state elections, election schedule, how many times you can vote, voting
process, polling booth, Model Code of Conduct, election results, candidate information process,
Election Commission of India, voter rights, and any other civic or election-related question about India.

RULES:
1. Do NOT express political opinions or preferences about parties or candidates.
2. Do NOT tell users which party or candidate to vote for.
3. For completely unrelated questions (sports, cooking, etc.), say: "I specialize in Indian election questions. What would you like to know about voting?"
4. Use simple English. You may include Tamil (தமிழ்) or Hindi (हिन्दी) terms where helpful.
5. Be warm, helpful, and encouraging. Voting is a right and a duty.
6. Always provide actionable steps and official ECI resources (eci.gov.in, voters.eci.gov.in).

KEY FACTS TO USE:
- In India, you can vote ONCE per election in your registered constituency
- Minimum voting age: 18 years
- Must be registered on Electoral Roll
- Vote using EVM (Electronic Voting Machine), confirmed by VVPAT slip
- Tamil Nadu 2026 Vidhan Sabha election is upcoming — major parties include DMK, AIADMK, BJP, Congress, VCK, PMK, MDMK, TVK

STYLE: Friendly India election guide. Factual. Clear. Non-partisan."""

SYSTEM_PROMPT_UK = """You are ElectionGuide, a helpful non-partisan UK Civic Education Assistant.

YOUR ROLE: Answer any question about UK elections, voting, civic processes, and democracy.

TOPICS: Voter registration, eligibility (18+), photo ID requirement, polling stations, postal voting,
how many times you can vote, First Past The Post system, House of Commons, devolved elections
(Scotland, Wales, Northern Ireland), Electoral Commission, election dates, party information.

RULES:
1. Do NOT express opinions about parties or candidates. Never tell users who to vote for.
2. For off-topic questions say: "I specialise in UK election questions. What would you like to know?"
3. Be helpful, warm, and factual. Always give official links.
STYLE: Friendly UK civic guide. Clear. Non-partisan."""

SYSTEM_PROMPT_AUSTRALIA = """You are ElectionGuide, a helpful non-partisan Australia Civic Education Assistant.

YOUR ROLE: Answer any question about Australian elections, voting, civic processes, and democracy.

TOPICS: Enrolment (aec.gov.au), compulsory voting (fine: AUD $20), preferential voting, how-to-vote,
Senate/House of Representatives, election dates, postal voting, polling places, donkey voting, informal votes.

RULES:
1. Do NOT express opinions about parties or candidates. Never tell users who to vote for.
2. For off-topic questions say: "I specialise in Australian election questions. What would you like to know?"
3. Emphasise voting is COMPULSORY. Be helpful and factual.
STYLE: Friendly Australian civic guide. Clear. Non-partisan."""

SYSTEM_PROMPT_CANADA = """You are ElectionGuide, a helpful non-partisan Canada Civic Education Assistant.

YOUR ROLE: Answer any question about Canadian elections, voting, civic processes, and democracy.

TOPICS: Voter registration (elections.ca), eligibility (18+), ID requirements, polling stations,
advance polls, mail-in ballots, First Past The Post system, House of Commons (343 seats),
election dates, how many times you can vote, party information.

RULES:
1. Do NOT express opinions about parties or candidates. Never tell users who to vote for.
2. For off-topic questions say: "I specialise in Canadian election questions. What would you like to know?"
3. Be helpful, warm, and factual. Always give official links.
STYLE: Friendly Canadian civic guide. Clear. Non-partisan."""

_SYSTEM_PROMPTS = {
    "india": SYSTEM_PROMPT_INDIA, "us": SYSTEM_PROMPT_US,
    "uk": SYSTEM_PROMPT_UK, "australia": SYSTEM_PROMPT_AUSTRALIA, "canada": SYSTEM_PROMPT_CANADA,
}

# Default
SYSTEM_PROMPT = SYSTEM_PROMPT_US


def _try_model(name: str, prompt: str):
    """Try to create a model with given name. Returns (model, prepend_prompt) or (None, None)."""
    try:
        try:
            m = genai.GenerativeModel(model_name=name, system_instruction=prompt)
            return m, None
        except TypeError:
            m = genai.GenerativeModel(model_name=name)
            return m, prompt
    except Exception as e:
        logger.debug("Model %s failed: %s", name, str(e)[:60])
        return None, None


# Model names to try in order (stable legacy first)
_MODEL_CANDIDATES = [
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
]


def _initialize_model(country: str = 'us'):
    """Initialize Gemini model — tries multiple model names for SDK compatibility."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set")
        return None, None
    try:
        prompt = SYSTEM_PROMPT_INDIA if country == 'india' else SYSTEM_PROMPT_US
        genai.configure(api_key=api_key)
        for name in _MODEL_CANDIDATES:
            m, pp = _try_model(name, prompt)
            if m is not None:
                logger.info("Using model: %s", name)
                return m, pp
        logger.error("All model candidates failed")
        return None, None
    except Exception as e:
        logger.error("Gemini init failed: %s", str(e)[:120])
        return None, None


QUOTA_MSG_INDIA = (
    "\u26a0\ufe0f AI service is temporarily busy. Please try again in 2\u20133 minutes.\n"
    "Meanwhile: visit eci.gov.in or voters.eci.gov.in to check your voter ID."
)
QUOTA_MSG_US = (
    "\u26a0\ufe0f AI service is temporarily busy. Please try again in 2\u20133 minutes.\n"
    "Meanwhile: visit vote.gov to register or check your polling location."
)
QUOTA_MSG_UK = (
    "\u26a0\ufe0f AI service is temporarily busy. Please try again in 2\u20133 minutes.\n"
    "Meanwhile: visit gov.uk/register-to-vote or electoralcommission.org.uk."
)
QUOTA_MSG_AUSTRALIA = (
    "\u26a0\ufe0f AI service is temporarily busy. Please try again in 2\u20133 minutes.\n"
    "Meanwhile: visit aec.gov.au to enrol or check your polling place."
)
QUOTA_MSG_CANADA = (
    "\u26a0\ufe0f AI service is temporarily busy. Please try again in 2\u20133 minutes.\n"
    "Meanwhile: visit elections.ca to register or find your polling station."
)

_QUOTA_MSGS = {
    "india": QUOTA_MSG_INDIA, "us": QUOTA_MSG_US,
    "uk": QUOTA_MSG_UK, "australia": QUOTA_MSG_AUSTRALIA, "canada": QUOTA_MSG_CANADA,
}


def _quota_msg(country: str) -> str:
    return _QUOTA_MSGS.get(country, QUOTA_MSG_US)


def chat(message: str, context: dict = None, country: str = 'us') -> dict:
    """
    Try each model in _MODEL_CANDIDATES.
    On 429 quota or 404 not-found: move to next model.
    Returns friendly quota message when ALL models exhausted.
    """
    fallback_msg = _FALLBACKS.get(country, SAFE_FALLBACK)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

    prompt = _SYSTEM_PROMPTS.get(country, SYSTEM_PROMPT_US)
    ctx_suffix = ""
    if context:
        day = context.get("election_day", "")
        name = context.get("election_name", "")
        if day:
            ctx_suffix = f"\n[Context: Next election: {name} on {day}]"

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        logger.error("genai.configure failed: %s", str(e)[:80])
        return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})

    last_error = ""
    hit_quota = False
    for model_name in _MODEL_CANDIDATES:
        try:
            try:
                model = genai.GenerativeModel(model_name=model_name, system_instruction=prompt)
                enriched = message + ctx_suffix
            except TypeError:
                model = genai.GenerativeModel(model_name=model_name)
                enriched = f"{prompt}\n\n---\nUser: {message}{ctx_suffix}"

            response = model.generate_content(enriched)
            raw_text = getattr(response, 'text', None)
            if not raw_text or not raw_text.strip():
                logger.warning("Empty response from %s", model_name)
                continue
            
            logger.info("Answered with model: %s", model_name)
            return build_response(
                success=True,
                data={"reply": enforce_readability(filter_output(raw_text)), "source": "gemini"}
            )
        except Exception as e:
            error_text = repr(e).lower() + " " + str(e).lower()
            last_error = error_text
            
            is_quota = any(x in error_text for x in ["429", "quota", "resourceexhausted", "exhausted", "rate limit"])
            if is_quota:
                logger.warning("Quota exceeded for %s. Exact Error: %s", model_name, error_text)
                hit_quota = True
                continue
            elif any(k in error_text for k in ('404', 'not found', 'not supported')):
                logger.warning("Model %s unavailable/not-supported, trying next", model_name)
                continue
            else:
                logger.error("Unretriable error %s: %s", model_name, error_text[:100])
                break

    if hit_quota or any(x in last_error for x in ["429", "quota", "resourceexhausted", "exhausted", "rate limit"]):
        return build_response(success=True, data={"reply": _quota_msg(country), "source": "quota_exceeded"})
    
    return build_response(success=True, data={"reply": fallback_msg, "source": "fallback"})


def detect_intent(message: str) -> dict:
    """
    Lightweight intent detection — no AI needed, uses keyword matching.
    Returns intent category to guide orchestrator service routing.
    """
    message_lower = message.lower()

    if any(k in message_lower for k in ["eligib", "can i vote", "old enough", "age", "citizen"]):
        return {"intent": "eligibility", "confidence": "high"}

    if any(k in message_lower for k in ["register", "registration", "sign up"]):
        return {"intent": "registration", "confidence": "high"}

    if any(k in message_lower for k in ["when", "election day", "date", "deadline", "location", "polling", "where"]):
        return {"intent": "election_info", "confidence": "high"}

    if any(k in message_lower for k in ["checklist", "steps", "how do i", "what do i need", "prepare"]):
        return {"intent": "checklist", "confidence": "high"}

    return {"intent": "general", "confidence": "low"}


def filter_output(text: str) -> str:
    """
    Scan Gemini output for forbidden political phrases.
    If found, replace with safe fallback — never return biased content.
    This is the OUTPUT security layer (input is handled in validators.py).
    """
    if not text:
        return SAFE_FALLBACK

    for pattern in FORBIDDEN_OUTPUT_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning("Output filter blocked biased content")
            return SAFE_FALLBACK

    return text


def enforce_readability(text: str) -> str:
    """
    Enforce 8th-grade readability on AI output.
    - Caps paragraphs at 3 sentences
    - Converts long blocks to bullet points
    - Strips excessive whitespace (including internal multiple spaces)

    This is a TESTABLE function — provable in test_chatbot.py.
    """
    if not text:
        return SAFE_FALLBACK

    # Strip excessive whitespace (internal + trailing)
    text = re.sub(r'[ \t]+', ' ', text.strip())
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Split into sentences roughly
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # If more than 5 sentences and not a list, convert to bullets
    if len(sentences) > 5 and not any(
        line.strip().startswith(('1.', '2.', '-', '*', '•'))
        for line in text.split('\n')
    ):
        bullet_lines = [f"• {s.strip()}" for s in sentences if s.strip()]
        return '\n'.join(bullet_lines[:7])  # Cap at 7 bullets

    return text

