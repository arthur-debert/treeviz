"""
Text and terminal output formatter using Jinja2 templates.
"""

from pathlib import Path
from typing import Any, Dict, Optional, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..base import Renderer, OutputFormat
from ..message import Message, MessageLevel


class TextFormatter(Renderer):
    """Formatter for text and terminal output using templates."""

    def __init__(
        self,
        template_dirs: Optional[List[Path]] = None,
        custom_filters: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the text formatter.

        Args:
            template_dirs: List of template directories to search
            custom_filters: Additional filters to register
        """
        if template_dirs is None:
            # Default to built-in templates
            template_dirs = [Path(__file__).parent.parent / "templates"]

        self.env = Environment(
            loader=FileSystemLoader([str(d) for d in template_dirs]),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.custom_filters = custom_filters or {}

        # Register custom filters
        self._register_filters()

    def _register_filters(self):
        """Register custom Jinja2 filters."""
        # Register custom filters first
        for name, filter_func in self.custom_filters.items():
            self.env.filters[name] = filter_func

        # Color filters for terminal output
        self.env.filters["red"] = lambda text: f"\033[91m{text}\033[0m"
        self.env.filters["green"] = lambda text: f"\033[92m{text}\033[0m"
        self.env.filters["yellow"] = lambda text: f"\033[93m{text}\033[0m"
        self.env.filters["blue"] = lambda text: f"\033[94m{text}\033[0m"
        self.env.filters["gray"] = lambda text: f"\033[90m{text}\033[0m"
        self.env.filters["bold"] = lambda text: f"\033[1m{text}\033[0m"

        # Conditional color based on message level
        def colorize_by_level(text, level):
            if isinstance(level, MessageLevel):
                level = level.value
            colors = {
                "error": "red",
                "warning": "yellow",
                "success": "green",
                "info": "blue",
                "debug": "gray",
            }
            color_filter = self.env.filters.get(
                colors.get(level, ""), lambda x: x
            )
            return color_filter(text)

        self.env.filters["level_color"] = colorize_by_level

    def render(
        self,
        data: Any,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render data using a Jinja2 template.

        Args:
            data: The data to render
            template: Template name (defaults to "default" or type-specific)
            context: Additional context including format type

        Returns:
            Rendered text string
        """
        if context is None:
            context = {}

        # Determine template
        if template is None:
            if isinstance(data, Message):
                template = "message.j2"
            else:
                template = "default.j2"

        # Determine if we should use colors
        output_format = context.get("format", OutputFormat.TEXT)
        use_colors = output_format == OutputFormat.TERM

        # Build template context
        template_context = {
            "data": data,
            "use_colors": use_colors,
            "format": output_format,
            **context,
        }

        # Apply color filters conditionally
        if not use_colors:
            # Override color filters to be no-ops
            for filter_name in [
                "red",
                "green",
                "yellow",
                "blue",
                "gray",
                "bold",
                "level_color",
            ]:
                self.env.filters[filter_name] = lambda text, *args: text

        # Add any globals from context
        if "_globals" in context:
            for name, func in context["_globals"].items():
                self.env.globals[name] = func

        # Add any filters from context
        if "_filters" in context:
            for name, func in context["_filters"].items():
                self.env.filters[name] = func

        # Render template
        tmpl = self.env.get_template(template)
        return tmpl.render(template_context)
