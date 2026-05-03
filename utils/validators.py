import re
from typing import Optional, Any


def sanitize_text(text: Optional[str]) -> str:
    """
    Basic text cleanup, whitespace stripping, and primitive HTML tag removal.

    Args:
        text (Optional[str]): The raw input text.

    Returns:
        str: The sanitized string.
    """
    if not text:
        return ""
    # Strip primitive HTML tags for defense in depth
    clean_html = re.sub(r"<[^>]+>", "", text)
    return clean_html.strip()


def validate_age(age: Any) -> Optional[int]:
    """
    Strict integer validation for age.

    Args:
        age (Any): The user-provided age.

    Returns:
        Optional[int]: The parsed integer age if valid (0-120), else None.
    """
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 120:
            return None
        return age_int
    except (ValueError, TypeError):
        return None


def check_jailbreak_attempt(text: Optional[str]) -> bool:
    """
    Heuristic check for common prompt injection or jailbreak patterns.

    Args:
        text (Optional[str]): The user input message.

    Returns:
        bool: True if a jailbreak attempt is detected, False otherwise.
    """
    if not text:
        return False

    patterns = [
        r"ignore previous instructions",
        r"reveal (your)? system prompt",
        r"you are now a",
        r"as a model",
        r"forget what I said",
        r"show me the code behind",
    ]

    content = text.lower()
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False


def validate_payload_size(text: str, max_chars: int = 500) -> bool:
    """
    Ensure the input text does not exceed the maximum allowed length.

    Args:
        text (str): The input payload text.
        max_chars (int): The maximum allowed characters.

    Returns:
        bool: True if payload size is within limits.
    """
    if not text:
        return True
    return len(text) <= max_chars


def contains_pii(text: Optional[str]) -> bool:
    """
    Check for potential Personally Identifiable Information (Emails/Phones).

    Args:
        text (Optional[str]): The input text to scan.

    Returns:
        bool: True if PII is detected, False otherwise.
    """
    if not text:
        return False

    # Enhanced PII patterns
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\+?\b\d{1,3}?[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"

    if re.search(email_pattern, text) or re.search(phone_pattern, text):
        return True
    return False
