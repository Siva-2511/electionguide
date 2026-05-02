"""
gemini_logic.py

Production-Grade Gemini integration for ElectionGuide.
Focus: Elite Reliability (Health Tracking, Discovery Caching, and Fault Tolerance).
"""

import os
import re
import logging
import hashlib
import threading
import time
import atexit
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from google import genai
from google.genai import types
from utils.response import build_response

logger = logging.getLogger(__name__)

# -----------------------
# PRODUCTION SETTINGS
# -----------------------
CACHE_VERSION = "v3"
_CACHE_MAX = 500
_GEMINI_TIMEOUT = 10
_MAX_RETRIES = 1
_FAILURE_THRESHOLD = 3
_FAILURE_COOLDOWN = 15
_DISCOVERY_CACHE_TTL = 600  # 10 Minutes
_MODEL_HEALTH_TTL = 300     # 5 Minutes

# Global Resilience State
_consecutive_failures = 0
_last_total_failure_time = 0
_resiliency_lock = threading.Lock()

# Discovery & Health Cache
_model_list_cache = {"data": None, "time": 0}
_model_health = {} # {model_name: last_fail_time}

_executor = ThreadPoolExecutor(max_workers=4)
atexit.register(lambda: _executor.shutdown(wait=False))

# -----------------------
# MODEL HIERARCHY
# -----------------------
STABLE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# -----------------------
# Fallbacks
# -----------------------
FALLBACKS = {
    "india": (
        "Namaste! I'm your India Election Guide. I can help with voter registration, "
        "eligibility (18+), EVM voting steps, and election schedules. "
        "What would you like to know? / आप क्या जानना चाहते हैं?"
    ),
    "us": (
        "I'm your US Election Guide. I can help with voter registration, eligibility, "
        "voting steps, and election dates. What would you like to know?"
    ),
}
SAFE_FALLBACK = FALLBACKS["us"]

SYSTEM_PROMPTS = {
    "india": "Non-partisan India election assistant. Use only ECI sources (eci.gov.in).",
    "us": "Non-partisan US election assistant. Use vote.gov only.",
}

# -----------------------
# Cache (Thread-safe)
# -----------------------
_cache = OrderedDict()
_cache_lock = threading.Lock()

# -----------------------
# Client
# -----------------------
def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key) if api_key else None

# -----------------------
# Discovery (Cached & Health-Aware)
# -----------------------
def _get_resilient_models(client):
    global _model_list_cache
    now = time.time()
    
    # 1. Update Discovery Cache if stale
    if now - _model_list_cache["time"] > _DISCOVERY_CACHE_TTL or not _model_list_cache["data"]:
        try:
            listed = client.models.list() or []
            found = [m.name.replace("models/", "") for m in listed if "flash" in m.name.lower()]
            _model_list_cache["data"] = list(dict.fromkeys(STABLE_MODELS + found))
            _model_list_cache["time"] = now
            logger.info("Model discovery cache refreshed.")
        except Exception as e:
            logger.info("Discovery refresh failed, using hierarchy: %s", e)
            if not _model_list_cache["data"]:
                _model_list_cache["data"] = STABLE_MODELS

    # 2. Filter by Health
    with _resiliency_lock:
        healthy_models = []
        for m in _model_list_cache["data"]:
            last_fail = _model_health.get(m, 0)
            if now - last_fail > _MODEL_HEALTH_TTL:
                healthy_models.append(m)
        
        return healthy_models or STABLE_MODELS[:2] # Always try at least some

# -----------------------
# Extraction & Filters
# -----------------------
def _extract_text(resp):
    try:
        if getattr(resp, "text", None):
            return resp.text
        candidates = getattr(resp, "candidates", [])
        if candidates and hasattr(candidates[0], "content"):
            parts = getattr(candidates[0].content, "parts", [])
            if parts:
                return getattr(parts[0], "text", "")
    except Exception:
        pass
    return ""

def filter_output(text: str, country: str = "us"):
    if not text: return ""
    patterns = [
        r"\byou should vote for\b", r"\bbest candidate\b", r"\bbest choice\b",
        r"\bthe winner will be\b", r"\bsupport the \w+ party\b",
        r"\byou must choose\b", r"\bvote for candidate\b",
    ]
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            logger.warning("Safety violation: %s", p)
            return FALLBACKS.get(country, SAFE_FALLBACK)
    return text

def enforce_readability(text: str):
    if not text: return ""
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > 5:
        return "\n".join(f"• {s.strip()}" for s in sentences[:7] if s.strip())
    return text

# -----------------------
# SMART EXECUTION
# -----------------------
def _call_gemini_smart(client, model, prompt, system_instruction):
    def task():
        return client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=400,
            ),
        )

    for attempt in range(_MAX_RETRIES + 1):
        future = _executor.submit(task)
        try:
            return future.result(timeout=_GEMINI_TIMEOUT)
        except TimeoutError:
            future.cancel()
            logger.info("Timeout: %s", model)
        except Exception as e:
            err = str(e).lower()
            if "404" in err or "not found" in err:
                raise Exception("MODEL_NOT_FOUND")
            if "429" in err or "rate" in err:
                time.sleep(2 * (attempt + 1))
            else:
                logger.info("Error: %s (%s)", model, type(e).__name__)
        if attempt < _MAX_RETRIES: time.sleep(1)

    raise Exception("MODEL_FAILED")

# -----------------------
# MAIN CHAT
# -----------------------
def chat(message: str, context=None, country="us"):
    global _consecutive_failures, _last_total_failure_time, _model_health
    start_time = time.time()
    raw = (message or "").strip()
    country = (country or "us").lower()
    fallback = FALLBACKS.get(country, SAFE_FALLBACK)

    if not raw:
        return build_response(True, {"reply": fallback, "source": "fallback"})

    # CIRCUIT BREAKER
    with _resiliency_lock:
        if _consecutive_failures >= _FAILURE_THRESHOLD:
            if time.time() - _last_total_failure_time < _FAILURE_COOLDOWN:
                return build_response(True, {"reply": fallback, "source": "circuit_breaker"})
            _consecutive_failures = 0

    normalized = " ".join(raw.lower().split())
    ctx_id = context.get("election_day") if context else ""
    cache_key = hashlib.md5(f"{CACHE_VERSION}:{country}:{normalized}:{ctx_id}".encode()).hexdigest()

    # 1. Cache Read
    with _cache_lock:
        if cache_key in _cache:
            _cache.move_to_end(cache_key)
            return build_response(True, _cache[cache_key].copy())

    client = _get_client()
    if not client: return build_response(True, {"reply": fallback, "source": "fallback"})

    prompt = raw
    if context and context.get("election_day"):
        prompt += f"\nElection date: {context['election_day']}"

    # RESILIENT LOOP
    models = _get_resilient_models(client)
    for model in models:
        try:
            resp = _call_gemini_smart(client, model, prompt, SYSTEM_PROMPTS.get(country, SYSTEM_PROMPTS["us"]))
            text = _extract_text(resp)
            
            if text and text.strip():
                result = {"reply": enforce_readability(filter_output(text, country)), "source": f"gemini:{model}"}
                
                with _resiliency_lock: _consecutive_failures = 0
                with _cache_lock:
                    _cache[cache_key] = result.copy()
                    _cache.move_to_end(cache_key)
                    if len(_cache) > _CACHE_MAX: _cache.popitem(last=False)

                logger.info("Success: %s (%.2fs)", model, time.time() - start_time)
                return build_response(True, result)

        except Exception as e:
            if str(e) != "MODEL_NOT_FOUND":
                with _resiliency_lock: _model_health[model] = time.time()
            logger.info("Failover: %s (%s)", model, str(e))
            continue

    # TOTAL FAILURE
    with _resiliency_lock:
        _consecutive_failures += 1
        _last_total_failure_time = time.time()
    
    return build_response(True, {"reply": fallback, "source": "total_failure"})

# -----------------------
# INTENT DETECTION
# -----------------------
def detect_intent(message: str) -> dict:
    msg = (message or "").lower()
    if "register" in msg: return {"intent": "voter_registration", "confidence": "high"}
    if "how" in msg or "steps" in msg: return {"intent": "voter_checklist", "confidence": "medium"}
    if "vote" in msg or "eligible" in msg: return {"intent": "eligibility", "confidence": "high"}
    return {"intent": "general", "confidence": "low"}
