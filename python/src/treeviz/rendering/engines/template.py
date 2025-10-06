"""
Template-based renderer that delegates to clier for actual rendering.

This is a compatibility wrapper that maintains the old API but uses
clier's rendering system internally.
"""

from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..presentation import Presentation

from clier.rendering import render as clier_render

from .base import BaseRenderer
from ...model import Node
from ..tree_formatter import TreeFormatter


class TemplateRenderer(BaseRenderer):
    """Template-based renderer implementation using clier."""

    def __init__(self):
        """Initialize the template renderer."""
        self.formatter = TreeFormatter()

    def render(
        self,
        node: Node,
        presentation: Optional["Presentation"] = None,
        symbols: Optional[Dict[str, str]] = None,
        use_color: Optional[bool] = None,
        terminal_width: Optional[int] = None,
    ) -> str:
        """
        Render a Node tree using templates.

        This renderer delegates to clier's rendering system.

        Args:
            node: Root node to render
            presentation: Presentation object with rendering configuration
            symbols: Pre-resolved icon map (if None, will be resolved)
            use_color: Whether to use color (if None, will auto-detect)
            terminal_width: Terminal width (if None, will use from presentation)

        Returns:
            Formatted string representation of the tree
        """
        # Prepare context using the formatter
        context = self.formatter.prepare_context(
            node=node,
            presentation=presentation,
            symbols=symbols,
            use_color=use_color,
            terminal_width=terminal_width,
        )

        # Determine output format based on color usage
        output_format = "term" if context.get("use_color", False) else "text"

        # Use clier's rendering with treeviz templates
        result = clier_render(
            data=node,
            format=output_format,
            template="tree.j2",
            context=context,
            template_dirs=[self.formatter.template_dir],
        )

        return result.rstrip()

    def supports_format(self, format: str) -> bool:
        """Template renderer supports text and term formats."""
        return format in ("text", "term")
