"""
Rendering package for treeviz.

This package provides template-based rendering with theme support
for tree visualization.
"""

from typing import Optional, Dict, Any

from .engines.template import TemplateRenderer
from .engines.base import BaseRenderer
from ..model import Node
from ..const import ICONS as DEFAULT_SYMBOLS
from .presentation import (
    Presentation,
    ViewOptions,
    ShowTypes,
    CompactMode,
)
from .presentation_loader import PresentationLoader


# For backward compatibility with the old API
def render(node: Node, options: Optional[Dict[str, Any]] = None) -> str:
    """
    Render a Node tree to text format.

    Args:
        node: Root node to render
        options: Optional dict with rendering options

    Returns:
        Formatted string representation of the tree
    """
    renderer = TemplateRenderer()
    # Default to text format for backward compatibility
    if options is None:
        options = {"format": "text", "symbols": DEFAULT_SYMBOLS}
    else:
        options = dict(options)  # Make a copy
        if "format" not in options:
            options["format"] = "text"
        if "symbols" not in options:
            options["symbols"] = DEFAULT_SYMBOLS
    return renderer.render(node, options)


def create_render_options(
    symbols: Optional[Dict[str, str]] = None, terminal_width: int = 80
) -> Dict[str, Any]:
    """
    Create render options dict.

    Args:
        symbols: Optional symbol overrides
        terminal_width: Terminal width for formatting

    Returns:
        Options dict for renderer
    """
    options = {
        "symbols": symbols if symbols is not None else DEFAULT_SYMBOLS,
        "terminal_width": terminal_width,
        "format": "text",
    }
    return options


# Simple type for compatibility
RenderOptions = Dict[str, Any]


__all__ = [
    "BaseRenderer",
    "TemplateRenderer",
    "render",
    "create_render_options",
    "DEFAULT_SYMBOLS",
    "RenderOptions",
    "Presentation",
    "ViewOptions",
    "PresentationLoader",
    "ShowTypes",
    "CompactMode",
]
