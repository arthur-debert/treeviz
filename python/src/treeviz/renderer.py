"""
3viz Renderer

This module renders 3viz Node trees to the 3viz text format.
"""

from typing import Dict, Optional
from treeviz.model import Node
from treeviz.config import get_default_config

# Export DEFAULT_SYMBOLS for tests - load from config
DEFAULT_SYMBOLS = get_default_config()["icon_map"]


class Renderer:
    """
    Renders a Node tree to the 3viz text format.
    """

    def __init__(
        self, symbols: Optional[Dict[str, str]] = None, terminal_width: int = 80
    ):
        # Get default symbols from configuration
        default_config = get_default_config()
        self.symbols = default_config["icon_map"].copy()

        # Allow override of specific symbols
        if symbols:
            self.symbols.update(symbols)
        self.terminal_width = terminal_width

    def render(self, node: Node) -> str:
        """
        Render a Node tree.
        """
        lines = []
        self._render_node(node, lines)
        return "\n".join(lines)

    def _render_node(self, node: Node, lines: list[str], depth: int = 0):
        """
        Recursively render a Node.
        """
        indent = "  " * depth

        # Extract node properties
        node_type = node.type or "unknown"
        text = node.label
        children = node.children
        icon = node.icon
        count = node.content_lines if not children else len(children)

        # Get symbol (prefer explicit icon, fallback to type mapping)
        symbol = icon or self.symbols.get(node_type, self.symbols["unknown"])

        count_str = f"{count}L"

        # Truncate text
        preview = text.splitlines()[0] if text else ""

        # Build the prefix (no count)
        prefix = f"{indent}{symbol} {preview}"

        # Build the suffix
        suffix = count_str

        # Calculate available space for content
        available_content_width = (
            self.terminal_width - len(prefix) - len(suffix) - 2
        )
        available_content_width = max(10, available_content_width)

        if len(preview) > available_content_width:
            preview = preview[: available_content_width - 1] + "…"

        # Re-build the prefix with truncated preview
        prefix = f"{indent}{symbol} {preview}"

        padded_prefix = f"{prefix:<{self.terminal_width - len(suffix) - 2}}"

        lines.append(f"{padded_prefix}  {suffix}")

        for child in children:
            self._render_node(child, lines, depth + 1)
