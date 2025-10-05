"""
Column specification for the layout system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ColumnAlign(Enum):
    """Column alignment options."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


@dataclass
class ColumnSpec:
    """
    Defines how a column behaves in the layout.

    Attributes:
        content: The text content for this column
        width: Fixed width for this column (takes precedence)
        max_width: Maximum width for this column
        min_width: Minimum width for this column
        align: How to align the content within the column
        truncate: Whether to truncate content that exceeds width
        responsive: If True, this column fills remaining space
        style: Optional style name for theming (e.g., 'icon', 'label')
        separator: Separator string after this column (default: space)
    """

    content: str
    width: Optional[int] = None
    max_width: Optional[int] = None
    min_width: int = 0
    align: ColumnAlign = ColumnAlign.LEFT
    truncate: bool = True
    responsive: bool = False
    style: Optional[str] = None
    separator: str = " "

    def calculate_width(self) -> int:
        """
        Calculate the actual width needed for this column's content.

        Returns:
            The width needed, respecting min/max constraints
        """
        content_width = len(self.content)

        # Fixed width takes precedence
        if self.width is not None:
            return self.width

        # Apply constraints
        if self.max_width is not None:
            content_width = min(content_width, self.max_width)

        return max(content_width, self.min_width)
