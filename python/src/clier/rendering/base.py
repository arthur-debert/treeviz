"""
Base interfaces for the rendering system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class Renderer(ABC):
    """Abstract base class for renderers."""

    @abstractmethod
    def render(
        self,
        data: Any,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render the data to a string.

        Args:
            data: The data to render
            template: Optional template name to use
            context: Optional additional context

        Returns:
            Rendered string
        """
        pass


class OutputFormat(Enum):
    """Supported output formats."""

    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    TERM = "term"  # Terminal with colors/formatting

    @classmethod
    def detect(
        cls, format_str: Optional[str] = None, is_tty: Optional[bool] = None
    ) -> "OutputFormat":
        """
        Detect the appropriate output format.

        Args:
            format_str: Explicit format string (json, yaml, text, term)
            is_tty: Whether output is to a terminal (None = auto-detect)

        Returns:
            The detected output format
        """
        if format_str:
            format_lower = format_str.lower()
            if format_lower in ("json", "yaml", "text", "term"):
                return cls(format_lower)

        # Default to terminal if TTY, otherwise text
        if is_tty is None:
            import sys

            is_tty = sys.stdout.isatty()

        return cls.TERM if is_tty else cls.TEXT
