"""Xuehua - Language Learning Assistant - Error types and ToolResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class XuehuaError(Exception):
    """Base exception for Xuehua."""

    pass


class ConfigurationError(XuehuaError):
    """Configuration-related error."""

    pass


class ValidationError(XuehuaError):
    """Input validation error."""

    pass


class APIError(XuehuaError):
    """API communication error."""

    pass


class DatabaseError(XuehuaError):
    """Database operation error."""

    pass


class FileError(XuehuaError):
    """File operation error."""

    pass


@dataclass
class ToolResult:
    """Unified result type for Xuehua API calls.

    Attributes
    ----------
    success : bool
        Whether the operation succeeded.
    data : dict
        Result data payload.
    message : str
        Human-readable message.
    error : str or None
        Error message if success is False.
    """

    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return self.message or "OK"
        return f"Error: {self.error}"