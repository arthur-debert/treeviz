"""
Built-in definition files for treeviz.

This package contains JSON definition files for popular AST formats.
"""

from .model import AdapterDef
from .lib import AdapterLib

# No longer need to preload - new system loads on demand

__all__ = [
    "AdapterDef",
    "AdapterLib",
]
