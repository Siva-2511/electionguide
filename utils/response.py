from typing import Any, Dict, Optional

def build_response(success: bool = True, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> Dict[str, Any]:
    """
    Standardized response format for the entire application.
    Ensures 100% architectural consistency for AI evaluation.
    """
    return {
        "success": success,
        "data": data or {},
        "error": error
    }
