"""
Generic Jinja2 template engine for clier.

This provides a base template engine that applications can extend
with their own templates and filters.
"""

from pathlib import Path
from typing import Dict, Any, List, Callable

from jinja2 import Environment, FileSystemLoader, select_autoescape


class Jinja2Engine:
    """Generic Jinja2 template engine."""

    def __init__(
        self,
        template_dirs: List[Path],
        auto_reload: bool = True,
        trim_blocks: bool = True,
        lstrip_blocks: bool = True,
    ):
        """
        Initialize the Jinja2 engine.

        Args:
            template_dirs: List of directories to search for templates
            auto_reload: Whether to auto-reload templates on change
            trim_blocks: Whether to trim blocks
            lstrip_blocks: Whether to left-strip blocks
        """
        self.env = Environment(
            loader=FileSystemLoader([str(d) for d in template_dirs]),
            autoescape=select_autoescape(["html", "xml"]),
            auto_reload=auto_reload,
            trim_blocks=trim_blocks,
            lstrip_blocks=lstrip_blocks,
        )

    def add_filter(self, name: str, filter_func: Callable) -> None:
        """Add a custom filter to the environment."""
        self.env.filters[name] = filter_func

    def add_global(self, name: str, value: Any) -> None:
        """Add a global value/function to the environment."""
        self.env.globals[name] = value

    def render(
        self, template_name: str, context: Dict[str, Any], **kwargs
    ) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Context dictionary for the template
            **kwargs: Additional context values

        Returns:
            Rendered string
        """
        template = self.env.get_template(template_name)
        full_context = {**context, **kwargs}
        return template.render(full_context)
