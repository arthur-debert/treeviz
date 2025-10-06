"""
Base renderer interface for all rendering engines.
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..presentation import Presentation

from ...model import Node


class BaseRenderer(ABC):
    """Abstract base class for rendering engines."""

    @abstractmethod
    def render(
        self, node: Node, presentation: Optional["Presentation"] = None
    ) -> str:
        """
        Render a node tree to a string representation.

        Args:
            node: Root node to render
            presentation: Presentation object with rendering configuration

        Returns:
            String representation of the tree
        """
        pass

    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """
        Check if this renderer supports the given output format.

        Args:
            format: Output format ('term', 'text', etc.)

        Returns:
            True if format is supported
        """
        pass
