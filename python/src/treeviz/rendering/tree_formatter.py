"""
Tree formatter that prepares data for rendering.

This module prepares tree data and context for the clier rendering system.
It doesn't do any rendering itself - that's handled by clier.
"""

from pathlib import Path
from typing import Dict, Optional, Any

from ..model import Node
from .presentation import Presentation
from .simple_layout import calculate_column_widths
from .icon_resolver import get_icon_map_from_options
from clier.rendering.themes import get_console
from rich.text import Text
from .templates.filters import format_extras, truncate_text, ljust, rjust


class TreeFormatter:
    """Prepares tree data and context for rendering."""

    def __init__(self):
        """Initialize the tree formatter."""
        # Get the templates directory for treeviz
        self.template_dir = Path(__file__).parent / "templates"

    def prepare_context(
        self,
        node: Node,
        presentation: Optional[Presentation] = None,
        symbols: Optional[Dict[str, str]] = None,
        use_color: Optional[bool] = None,
        terminal_width: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Prepare the context for tree rendering.

        This prepares all the data and functions needed by the tree template.
        The actual rendering is done by clier's TextFormatter.

        Args:
            node: Root node to render
            presentation: Presentation object with rendering configuration
            symbols: Pre-resolved icon map (if None, will be resolved)
            use_color: Whether to use color (if None, will auto-detect)
            terminal_width: Terminal width (if None, will use from presentation)

        Returns:
            Context dictionary for template rendering
        """
        # Use default presentation if none provided
        if presentation is None:
            presentation = Presentation()

        # Extract view options
        view_opts = presentation.view

        # Use provided values or fall back to defaults
        if terminal_width is None:
            terminal_width = view_opts.max_width

        # Handle -1 as "use terminal width"
        if terminal_width == -1:
            import os

            try:
                terminal_width = os.get_terminal_size().columns
            except OSError:
                # Fallback if terminal size detection fails (e.g., when not in a real TTY)
                terminal_width = 80

        if use_color is None:
            # Default behavior if not specified
            import sys

            use_color = sys.stdout.isatty()

        if symbols is None:
            # Fall back to resolving icons if not provided
            symbols = get_icon_map_from_options(presentation)

        # Calculate column widths for the tree
        column_widths = calculate_column_widths(node, terminal_width)

        # Prepare context
        context = {
            "root_node": node,
            "symbols": symbols,
            "column_widths": column_widths,
            "use_color": use_color,
            "presentation": presentation,
            "view_options": view_opts,
            "terminal_width": terminal_width,
            # Pass globals and filters to clier
            "_globals": {
                "apply_simple_markup": self._create_markup_function(use_color),
            },
            "_filters": {
                "format_extras": format_extras,
                "truncate": truncate_text,
                "ljust": ljust,
                "rjust": rjust,
            },
        }

        return context

    def _create_markup_function(self, use_color: bool):
        """Create a markup function for the template."""
        if not use_color:
            # No-op function for plain text
            return lambda line, *args: line

        def apply_simple_markup(
            plain_line: str,
            indent_width: int,
            icon_str: str,
            label: str,
            extras_str: str,
            count_str: str,
        ) -> str:
            """Apply Rich markup to a formatted line."""
            # Get console for rendering
            console = get_console(force_terminal=False)

            # Create a Rich Text object from the plain line
            text = Text(plain_line)

            # Calculate positions based on what we know
            pos = indent_width

            # Style icon
            if icon_str:
                icon_end = pos + len(icon_str.rstrip())
                text.stylize("icon", pos, icon_end)
                pos = pos + len(icon_str)

            # Style label
            if label:
                # Find actual label in line (might be truncated)
                label_in_line = plain_line[pos:].split("  ")[0].rstrip()
                if label_in_line:
                    label_end = pos + len(label_in_line)
                    text.stylize("label", pos, label_end)

            # Style extras - search from the right
            if extras_str:
                extras_pos = plain_line.rfind(extras_str)
                if extras_pos >= 0:
                    text.stylize(
                        "extras", extras_pos, extras_pos + len(extras_str)
                    )

            # Style line count - it's the last element
            if count_str:
                count_pos = plain_line.rfind(count_str)
                if count_pos >= 0:
                    text.stylize(
                        "numlines", count_pos, count_pos + len(count_str)
                    )

            # Render with console (applies theme)
            with console.capture() as capture:
                console.print(text, end="")

            return capture.get()

        return apply_simple_markup
