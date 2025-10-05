"""
Rendering engines for treeviz.

Available engines:
- legacy: Traditional text-based renderer
- template: Jinja2-based renderer with Rich formatting
"""

from .base import BaseRenderer

__all__ = ["BaseRenderer"]
