"""
utils/response_guard.py
Hard schema enforcement decorator.
Applied to every service function to guarantee 100% contract compliance.
"""

import functools
from typing import Callable, Any
from utils.response import build_response


def enforce_schema(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that hard-enforces the unified response schema.

    If a service accidentally returns a plain dict, string, or None,
    this guard auto-wraps it — preventing silent schema drift.

    Args:
        func (Callable[..., Any]): The function to be decorated.

    Returns:
        Callable[..., Any]: The wrapped function ensuring a standardized response.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = func(*args, **kwargs)
            # Validate schema — must have all three keys
            if (
                isinstance(result, dict)
                and "success" in result
                and "data" in result
                and "error" in result
            ):
                return result
            # Auto-wrap non-compliant output
            return build_response(data=result if result is not None else {})
        except Exception as e:
            # Catch any unhandled service error — never expose raw exceptions
            return build_response(success=False, error=str(e))

    return wrapper
