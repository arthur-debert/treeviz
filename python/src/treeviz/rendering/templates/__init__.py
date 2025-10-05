"""
Templates for treeviz rendering.

This module contains Jinja2 templates and filters for rendering
treeviz trees with Rich formatting.
"""

from .filters import register_filters

__all__ = ["register_filters"]
