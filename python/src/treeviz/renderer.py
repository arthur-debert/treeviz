"""
3viz Renderer

This module renders 3viz Node trees to the 3viz text format using pure functions.
"""

from typing import Dict, Optional, List, NamedTuple
from treeviz.model import Node
from treeviz.config import get_default_config

# Export DEFAULT_SYMBOLS for tests - load from config
DEFAULT_SYMBOLS = get_default_config()["icon_map"]


class RenderOptions(NamedTuple):
    """Configuration options for rendering."""

    symbols: Dict[str, str]
    terminal_width: int


def create_render_options(
    symbols: Optional[Dict[str, str]] = None, terminal_width: int = 80
) -> RenderOptions:
    """
    Create render options with default symbols and custom overrides.

    Args:
        symbols: Optional custom symbol mapping
        terminal_width: Terminal width for formatting

    Returns:
        RenderOptions with merged symbols
    """
    # Get default symbols from configuration
    default_config = get_default_config()
    merged_symbols = default_config["icon_map"].copy()

    # Allow override of specific symbols
    if symbols:
        merged_symbols.update(symbols)

    return RenderOptions(symbols=merged_symbols, terminal_width=terminal_width)


def render(node: Node, options: Optional[RenderOptions] = None) -> str:
    """
    Render a Node tree to the 3viz text format.

    Args:
        node: Root node to render
        options: Render options (symbols and terminal width)

    Returns:
        Formatted string representation of the tree
    """
    if options is None:
        options = create_render_options()

    lines: List[str] = []
    _render_node(node, lines, options, depth=0)
    return "\n".join(lines)


def _render_node(
    node: Node, lines: List[str], options: RenderOptions, depth: int = 0
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
    symbol = icon or options.symbols.get(node_type, options.symbols["unknown"])

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
        _render_node(child, lines, options, depth + 1)
