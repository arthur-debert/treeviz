"""
YAML output formatter.
"""

from typing import Any, Dict, Optional

from .json_formatter import JSONFormatter

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class YAMLFormatter(JSONFormatter):
    """Formatter for YAML output."""

    def render(
        self,
        data: Any,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render data as YAML.

        Args:
            data: The data to render
            template: Ignored for YAML
            context: Optional context with flow_style setting

        Returns:
            YAML string
        """
        if not HAS_YAML:
            # Fallback to JSON if YAML not available
            return "# YAML output requires PyYAML\n" + super().render(
                data, template, context
            )

        # Convert to serializable form using parent's method
        serializable = self._make_serializable(data)

        # Get YAML options from context
        flow_style = False
        if context and "flow_style" in context:
            flow_style = context["flow_style"]

        return yaml.dump(
            serializable,
            default_flow_style=flow_style,
            allow_unicode=True,
            sort_keys=False,
        )
