"""Standard response envelope helpers."""
from __future__ import annotations

from typing import Any


def success_response(data: Any) -> dict:
    """Wrap data in a success envelope."""
    return {"status": "success", "data": data}


def error_response(message: str) -> dict:
    """Wrap an error message in an error envelope."""
    return {"status": "error", "error_message": message}
