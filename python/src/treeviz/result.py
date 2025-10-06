"""
Result objects for treeviz commands.
"""

from dataclasses import dataclass
from typing import Dict, Any

from .model import Node
from .rendering.presentation import Presentation


@dataclass
class TreeResult:
    """
    Result object for the viz command.

    Contains all the data needed to render a tree visualization.
    """

    node: Node
    presentation: Presentation
    symbols: Dict[str, str]
    use_color: bool
    terminal_width: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        from dataclasses import asdict

        return {
            "node": asdict(self.node),
            "presentation": asdict(self.presentation),
            "symbols": self.symbols,
            "use_color": self.use_color,
            "terminal_width": self.terminal_width,
        }
