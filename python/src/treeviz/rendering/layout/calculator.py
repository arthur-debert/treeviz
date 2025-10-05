"""
Layout calculator for column-based rendering.

This module implements the bidirectional layout algorithm that processes
fixed columns from the edges and gives remaining space to responsive columns.
"""

from typing import List

from .column import ColumnSpec, ColumnAlign


def layout_columns(columns: List[ColumnSpec], terminal_width: int) -> List[str]:
    """
    Layout columns with constraint-based positioning.

    Algorithm:
    1. Calculate fixed widths from left
    2. Calculate fixed widths from right
    3. Give remaining space to responsive column(s)
    4. Apply truncation and padding

    Args:
        columns: List of column specifications
        terminal_width: Available terminal width

    Returns:
        List of formatted column strings
    """
    if not columns:
        return []

    # Separate columns by type and position
    left_fixed = []
    right_fixed = []
    responsive_cols = []

    for i, col in enumerate(columns):
        if col.responsive:
            responsive_cols.append((i, col))
        elif col.align == ColumnAlign.RIGHT:
            right_fixed.append((i, col))
        else:  # LEFT or CENTER
            left_fixed.append((i, col))

    # Calculate fixed column widths
    fixed_widths = {}
    total_fixed_width = 0

    # Process left-aligned fixed columns
    for idx, col in left_fixed:
        width = col.calculate_width()
        fixed_widths[idx] = width
        total_fixed_width += width

    # Process right-aligned fixed columns
    for idx, col in right_fixed:
        width = col.calculate_width()
        fixed_widths[idx] = width
        total_fixed_width += width

    # Account for separators
    total_separator_width = sum(len(col.separator) for col in columns[:-1])
    total_fixed_width += total_separator_width

    # Calculate available space for responsive columns
    available_width = terminal_width - total_fixed_width

    # Distribute available width to responsive columns
    if responsive_cols:
        # Ensure we don't allocate negative or zero width
        responsive_width = max(1, available_width // len(responsive_cols))
        for idx, col in responsive_cols:
            fixed_widths[idx] = responsive_width

    # Ensure we have width for all columns
    for i in range(len(columns)):
        if i not in fixed_widths:
            fixed_widths[i] = 1  # Minimum width

    # Format each column
    formatted_columns = []
    for i, col in enumerate(columns):
        width = fixed_widths.get(i, col.calculate_width())
        formatted = _format_column(col, width)
        formatted_columns.append(formatted)

    return formatted_columns


def _format_column(col: ColumnSpec, width: int) -> str:
    """
    Format a single column to the specified width.

    Args:
        col: Column specification
        width: Target width for the column

    Returns:
        Formatted string
    """
    content = col.content

    # For now, use simple character counting
    # TODO: Handle Unicode display width properly
    content_len = len(content)

    # Truncate if needed
    if col.truncate and content_len > width:
        if width > 1:
            # Use single ellipsis character
            content = content[: width - 1] + "…"
        else:
            content = content[:width]

    # Apply alignment (using simple len for now)
    if col.align == ColumnAlign.LEFT:
        formatted = content.ljust(width)
    elif col.align == ColumnAlign.RIGHT:
        formatted = content.rjust(width)
    elif col.align == ColumnAlign.CENTER:
        formatted = content.center(width)
    else:
        formatted = content

    return formatted


def calculate_line_layout(
    indent: str,
    icon: str,
    label: str,
    extras: str,
    line_count: str,
    terminal_width: int,
) -> str:
    """
    Calculate the layout for a tree line using the column system.

    This is a convenience function that creates the standard column
    layout for treeviz output.

    Args:
        indent: Indentation string
        icon: Icon character
        label: Node label (responsive)
        extras: Extra metadata (optional)
        line_count: Line count string (e.g., "5L")
        terminal_width: Available terminal width

    Returns:
        Formatted line string
    """
    columns = []

    # Fixed left: indent + icon
    if indent or icon:
        columns.append(
            ColumnSpec(
                content=f"{indent}{icon}",
                align=ColumnAlign.LEFT,
                style="icon",
                separator=" " if icon else "",
            )
        )

    # Responsive: label
    columns.append(
        ColumnSpec(
            content=label,
            responsive=True,
            align=ColumnAlign.LEFT,
            style="label",
            separator="  ",  # Double space before right columns
        )
    )

    # Fixed right: extras (if present)
    if extras:
        columns.append(
            ColumnSpec(
                content=extras,
                max_width=20,
                align=ColumnAlign.RIGHT,
                style="extras",
                separator=" ",
            )
        )

    # Fixed right: line count
    columns.append(
        ColumnSpec(
            content=line_count,
            width=6,  # Fixed width for alignment
            align=ColumnAlign.RIGHT,
            style="numlines",
            separator="",  # Last column, no separator
        )
    )

    # Layout and join columns
    formatted = layout_columns(columns, terminal_width)

    # Join with separators
    result = ""
    for i, (col_str, col_spec) in enumerate(zip(formatted, columns)):
        result += col_str
        if i < len(columns) - 1:
            result += col_spec.separator

    # Ensure result doesn't exceed terminal width
    result = result.rstrip()
    if len(result) > terminal_width:
        result = result[: terminal_width - 1] + "…"

    return result
