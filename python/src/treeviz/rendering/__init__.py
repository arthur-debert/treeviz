"""
Rendering package for treeviz.

This package provides template-based rendering with theme support
for tree visualization.
"""

from .engines.template import TemplateRenderer
from .engines.base import BaseRenderer
from .presentation import (
    Presentation,
    ViewOptions,
    ShowTypes,
    CompactMode,
)
from .presentation_loader import PresentationLoader


__all__ = [
    "BaseRenderer",
    "TemplateRenderer",
    "Presentation",
    "ViewOptions",
    "PresentationLoader",
    "ShowTypes",
    "CompactMode",
]
