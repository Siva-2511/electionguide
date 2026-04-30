from typing import Optional, Any
import re

def sanitize_text(text: Optional[str]) -> str:
    """Basic text cleanup and whitespace stripping."""
    if not text:
        return ""
    return text.strip()

def validate_age(age: Any) -> Optional[int]:
    """Strict integer validation for age."""
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 120:
            return None
        return age_int
    except (ValueError, TypeError):
        return None

def check_jailbreak_attempt(text: Optional[str]) -> bool:
    """
    Heuristic check for common prompt injection/jailbreak patterns.
    Targets "Ignore instructions", "Reveal prompt", and "System status".
    """
    if not text:
        return False
    
    patterns = [
        r"ignore previous instructions",
        r"reveal (your)? system prompt",
        r"you are now a",
        r"as a model",
        r"forget what I said",
        r"show me the code behind"
    ]
    
    content = text.lower()
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False

def validate_payload_size(text: str, max_chars: int = 500) -> bool:
    """Return True if text is within acceptable size limits."""
    if not text:
        return True
    return len(text) <= max_chars


def contains_pii(text: Optional[str]) -> bool:
    """Simple check for emails or phone numbers to prevent logging/storage of PII."""
    if not text:
        return False
    
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b'
    
    if re.search(email_pattern, text) or re.search(phone_pattern, text):
        return True
    return False
