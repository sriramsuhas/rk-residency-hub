"""Small helper to keep success responses consistently shaped across the API."""
from typing import Any


def success(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data}
