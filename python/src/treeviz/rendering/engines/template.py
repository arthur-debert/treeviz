"""
Template-based renderer using Jinja2 and Rich.

This renderer uses templates to generate tree output with optional
Rich formatting for colored terminal output.
"""

from typing import Dict, Optional, Any, Tuple
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.text import Text

from .base import BaseRenderer
from ...model import Node
from ..themes import set_theme_mode, get_console
from ..layout.calculator import (
    calculate_line_layout,
    calculate_line_layout_with_positions,
)
from ..templates.filters import register_filters


class TemplateRenderer(BaseRenderer):
    """Template-based renderer implementation."""

    def __init__(self):
        """Initialize the template renderer."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        register_filters(self.env)

        # Add layout functions to globals
        self.env.globals["calculate_line_layout"] = calculate_line_layout
        self.env.globals["calculate_line_layout_with_positions"] = (
            calculate_line_layout_with_positions
        )
        self.env.globals["apply_rich_markup"] = self._apply_rich_markup
        self.env.globals["apply_rich_markup_with_positions"] = (
            self._apply_rich_markup_with_positions
        )

        # Theme is now accessed globally

    def render(
        self, node: Node, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a Node tree using templates.

        Args:
            node: Root node to render
            options: Rendering options including:
                - symbols: Dict of node type to icon mappings
                - terminal_width: Width of terminal (default 80)
                - format: Output format ('term' or 'text')
                - theme: Theme name or 'dark'/'light'

        Returns:
            Formatted string representation of the tree
        """
        if options is None:
            options = {}

        # Extract options
        symbols = options.get("symbols", {})
        terminal_width = options.get("terminal_width", 80)
        output_format = options.get("format", "term")
        theme_override = options.get("theme")

        # Override theme mode if specified
        if theme_override and theme_override in ("dark", "light"):
            set_theme_mode(theme_override)

        # Determine if we should use color
        use_color = output_format == "term"

        # Create render options object for template
        from .. import create_render_options

        render_options = create_render_options(symbols, terminal_width)

        # Get the template
        template = self.env.get_template("tree.j2")

        # Render with template
        result = template.render(
            root_node=node,
            render_options=render_options,
            terminal_width=terminal_width,
            use_color=use_color,
        )
        return result.rstrip()

    def supports_format(self, format: str) -> bool:
        """Template renderer supports text and term formats."""
        return format in ("text", "term")

    def _apply_rich_markup(
        self,
        plain_line: str,
        indent: str,
        icon: str,
        label: str,
        extras: str,
        count_str: str,
    ) -> str:
        """
        Apply Rich markup to a formatted line.

        This function takes the plain text line and the original components
        to apply semantic styling without changing the layout.

        Args:
            plain_line: The formatted line from calculate_line_layout
            indent: Indentation string
            icon: Icon character
            label: Node label
            extras: Formatted extras string
            count_str: Line count string (e.g., "3L")

        Returns:
            Line with Rich markup applied
        """
        # Get console for rendering with forced terminal mode for color output
        console = get_console(force_terminal=True)

        # Create a Rich Text object from the plain line
        text = Text(plain_line)

        # Find positions of components in the line
        current_pos = 0

        # Skip indent (no styling)
        current_pos += len(indent)

        # Style icon
        if icon:
            icon_start = current_pos
            icon_end = icon_start + len(icon)
            text.stylize("icon", icon_start, icon_end)
            current_pos = icon_end + 1  # Skip space after icon

        # Style label
        if label:
            # Find where label starts (after icon and space)
            label_start = plain_line.find(label, current_pos)
            if label_start >= 0:
                # Account for possible truncation with ellipsis
                label_in_line = plain_line[label_start:].split("  ")[0].rstrip()
                label_end = label_start + len(label_in_line)
                text.stylize("label", label_start, label_end)
                current_pos = label_end

        # Style extras (if present)
        if extras:
            # Extras are right-aligned before line count
            extras_start = plain_line.rfind(extras)
            if extras_start >= 0:
                extras_end = extras_start + len(extras)
                text.stylize("extras", extras_start, extras_end)

        # Style line count (last element)
        if count_str:
            count_start = plain_line.rfind(count_str)
            if count_start >= 0:
                count_end = count_start + len(count_str)
                text.stylize("numlines", count_start, count_end)

        # Render with console (applies theme)
        with console.capture() as capture:
            console.print(text, end="")

        return capture.get()

    def _apply_rich_markup_with_positions(
        self,
        plain_line: str,
        positions: Dict[str, Tuple[int, int]],
    ) -> str:
        """
        Apply Rich markup to a formatted line using pre-calculated positions.

        This is more efficient and robust than searching for components
        in the formatted string.

        Args:
            plain_line: The formatted line from calculate_line_layout
            positions: Dictionary mapping component names to (start, end) positions

        Returns:
            Line with Rich markup applied
        """
        # Get console for rendering with forced terminal mode for color output
        console = get_console(force_terminal=True)

        # Create a Rich Text object from the plain line
        text = Text(plain_line)

        # Apply styles using the pre-calculated positions
        for component, (start, end) in positions.items():
            if component == "indent":
                # No style for indent
                continue
            elif component in ("icon", "label", "extras", "numlines"):
                # Apply the component style
                text.stylize(component, start, end)

        # Render with console (applies theme)
        with console.capture() as capture:
            console.print(text, end="")

        return capture.get()
