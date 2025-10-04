"""
Built-in definition files for treeviz.

This package contains JSON definition files for popular AST formats.
"""

from .model import AdapterDef
from .lib import Lib

# Load core libraries on module import
Lib.load_core_libs()

__all__ = [
    "AdapterDef",
    "Lib",
]
