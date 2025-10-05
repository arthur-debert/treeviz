"""
Legacy text-based renderer.

This is the original treeviz renderer, moved here to maintain backward compatibility
while we implement the new template-based system.
"""

from typing import Dict, Optional, List, NamedTuple, Any

from .base import BaseRenderer
from ...model import Node
from ...const import ICONS


# Export DEFAULT_SYMBOLS for tests - use const baseline
DEFAULT_SYMBOLS = ICONS


class RenderOptions(NamedTuple):
    """Configuration options for rendering."""

    symbols: Dict[str, str]
    terminal_width: int


class LegacyRenderer(BaseRenderer):
    """Legacy text-based renderer implementation."""

    def render(
        self, node: Node, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a Node tree to the 3viz text format.

        Args:
            node: Root node to render
            options: Dict with 'symbols' and 'terminal_width' keys

        Returns:
            Formatted string representation of the tree
        """
        # Convert dict options to RenderOptions
        render_options = self._create_render_options(options)

        lines: List[str] = []
        self._render_node(node, lines, render_options, depth=0)
        return "\n".join(lines)

    def supports_format(self, format: str) -> bool:
        """Legacy renderer supports text and term formats."""
        return format in ("text", "term")

    def _create_render_options(
        self, options: Optional[Dict[str, Any]] = None
    ) -> RenderOptions:
        """
        Create render options with default symbols and custom overrides.

        Args:
            options: Optional dict with rendering options

        Returns:
            RenderOptions with merged symbols
        """
        if options is None:
            options = {}

        symbols = options.get("symbols")
        terminal_width = options.get("terminal_width", 80)

        # Start with baseline icons from const.py
        merged_symbols = ICONS.copy()

        # Allow override of specific symbols
        if symbols:
            merged_symbols.update(symbols)

        return RenderOptions(
            symbols=merged_symbols, terminal_width=terminal_width
        )

    def _render_node(
        self,
        node: Node,
        lines: List[str],
        options: RenderOptions,
        depth: int = 0,
    ) -> None:
        """
        Recursively render a single node and its children.

        Args:
            node: Node to render
            lines: List to append rendered lines to
            options: Render options
            depth: Current depth for indentation
        """
        indent = "  " * depth

        # Extract node properties
        node_type = node.type or "unknown"
        text = node.label
        children = node.children
        icon = node.icon
        count = node.content_lines if not children else len(children)

        # Get symbol (prefer explicit icon, fallback to type mapping)
        symbol = icon or options.symbols.get(
            node_type, options.symbols["unknown"]
        )

        count_str = f"{count}L"

        # Truncate text
        preview = text.splitlines()[0] if text else ""

        # Build the prefix (no count)
        prefix = f"{indent}{symbol} {preview}"

        # Build the suffix
        suffix = count_str

        # Calculate available space for content
        available_content_width = (
            options.terminal_width - len(prefix) - len(suffix) - 2
        )
        available_content_width = max(10, available_content_width)

        if len(preview) > available_content_width:
            preview = preview[: available_content_width - 1] + "…"

        # Re-build the prefix with truncated preview
        prefix = f"{indent}{symbol} {preview}"

        padded_prefix = f"{prefix:<{options.terminal_width - len(suffix) - 2}}"

        lines.append(f"{padded_prefix}  {suffix}")

        for child in children:
            self._render_node(child, lines, options, depth + 1)


# Compatibility functions to match old API
def create_render_options(
    symbols: Optional[Dict[str, str]] = None, terminal_width: int = 80
) -> RenderOptions:
    """
    Create render options with default symbols and custom overrides.
    Maintained for backward compatibility.
    """
    merged_symbols = ICONS.copy()
    if symbols:
        merged_symbols.update(symbols)
    return RenderOptions(symbols=merged_symbols, terminal_width=terminal_width)


def render(node: Node, options: Optional[RenderOptions] = None) -> str:
    """
    Render a Node tree to the 3viz text format.
    Maintained for backward compatibility.
    """
    renderer = LegacyRenderer()
    if options:
        dict_options = {
            "symbols": options.symbols,
            "terminal_width": options.terminal_width,
        }
    else:
        dict_options = None
    return renderer.render(node, dict_options)
