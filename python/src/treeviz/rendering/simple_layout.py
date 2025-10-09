"""
Simple layout calculator for tree rendering.

Just calculates column widths and passes them to templates.
"""

from dataclasses import dataclass

from ..model import Node


@dataclass
class ColumnWidths:
    """Calculated column widths for tree layout."""

    indent_width: int
    icon_width: int
    label_width: int
    extras_width: int
    count_width: int


def calculate_column_widths(
    root: Node,
    terminal_width: int = 80,
    icon_width: int = 2,  # icon + space
    count_suffix: str = "L",
) -> ColumnWidths:
    """
    Calculate column widths for the entire tree.

    Args:
        root: Root node of the tree
        terminal_width: Available terminal width
        icon_width: Width reserved for icon + space
        count_suffix: Suffix for line counts (e.g. "L")

    Returns:
        ColumnWidths with calculated values
    """
    # Calculate max widths needed
    max_indent = 0
    max_extras = 0
    max_count = 0

    def analyze_node(node: Node, depth: int = 0):
        nonlocal max_indent, max_extras, max_count

        # Track indent depth
        max_indent = max(max_indent, depth * 2)  # 2 spaces per level

        # Track extras width
        if node.extra:
            # Format extras as "key=value key2=value2"
            extras_parts = []
            for k, v in node.extra.items():
                if v is True:
                    extras_parts.append(k)
                elif v not in (False, None):
                    extras_parts.append(f"{k}={v}")
            extras_str = " ".join(extras_parts)
            # Account for truncation at 20 chars
            extras_len = min(20, len(extras_str))
            max_extras = max(max_extras, extras_len)

        # Track line count width
        line_count = len(node.children) if node.children else node.content_lines
        count_str = f"{line_count}{count_suffix}"
        max_count = max(max_count, len(count_str))

        # Recurse
        if node.children:
            for child in node.children:
                analyze_node(child, depth + 1)

    analyze_node(root)

    # Add padding
    if max_extras > 0:
        max_extras += 2  # spaces around extras
    max_count += 1  # space before count

    # Calculate available space for narrow terminals
    min_required = (
        max_indent + icon_width + 1 + max_count
    )  # 1 char for label minimum

    if terminal_width <= min_required + max_extras:
        # Very narrow terminal - skip extras entirely
        max_extras = 0

    # Calculate label width as remaining space
    # Note: We don't include max_indent in fixed_width because indent varies per line
    # The line count should end exactly at terminal_width
    fixed_width = icon_width + max_extras + max_count
    # For very narrow terminals, we need at least 1 char for label
    label_width = max(1, terminal_width - fixed_width - max_indent)

    return ColumnWidths(
        indent_width=max_indent,
        icon_width=icon_width,
        label_width=label_width,
        extras_width=max_extras,
        count_width=max_count,
    )
