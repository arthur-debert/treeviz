"""
Built-in definition files for treeviz.

This package contains JSON definition files for popular AST formats.
"""

from .model import AdapterDef
from .lib import AdapterLib

# Load built-in and user libraries on module import
AdapterLib.load_core_libs()
AdapterLib.load_user_libs()

__all__ = [
    "AdapterDef",
    "AdapterLib",
]
