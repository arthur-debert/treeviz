"""
Built-in definition files for treeviz.

This package contains JSON definition files for popular AST formats.
"""

from .definitions import (
    load_def,
    validate_def,
    get_default_def,
    load_format_def,
)
from .schema import Definition
from .lib import Lib

# Load core libraries on module import
Lib.load_core_libs()

__all__ = [
    "load_def",
    "validate_def",
    "get_default_def",
    "load_format_def",
    "Definition",
    "Lib",
]
