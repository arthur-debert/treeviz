"""
3viz Renderer - Compatibility wrapper.

This module provides backward compatibility while we transition to the new
rendering system. It re-exports the legacy renderer's API.
"""

# Re-export everything from legacy renderer for backward compatibility
from .rendering.engines.legacy import (
    DEFAULT_SYMBOLS,
    RenderOptions,
    create_render_options,
    render,
)

__all__ = [
    "DEFAULT_SYMBOLS",
    "RenderOptions",
    "create_render_options",
    "render",
]
