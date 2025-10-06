"""
JSON output formatter.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import asdict, is_dataclass

from ..base import Renderer


class JSONFormatter(Renderer):
    """Formatter for JSON output."""

    def render(
        self,
        data: Any,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render data as JSON.

        Args:
            data: The data to render
            template: Ignored for JSON
            context: Optional context with indent setting

        Returns:
            JSON string
        """
        indent = 2
        if context and "indent" in context:
            indent = context["indent"]

        # Convert dataclasses to dicts
        serializable = self._make_serializable(data)

        return json.dumps(serializable, indent=indent, ensure_ascii=False)

    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable form."""
        if is_dataclass(obj) and not isinstance(obj, type):
            # Use to_dict method if available, otherwise asdict
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            return asdict(obj)
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            # Convert arbitrary objects to dict
            return {
                k: self._make_serializable(v)
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        else:
            return obj
