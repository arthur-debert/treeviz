"""
Document format parsing for treeviz.

This module provides format-agnostic document parsing that converts
various input formats (JSON, YAML, XML, etc.) into Python objects
that can then be processed by adapters.
"""

from .model import Format, DocumentFormatError
from .parser import parse_document, register_format, get_supported_formats

__all__ = [
    "Format",
    "DocumentFormatError",
    "parse_document",
    "register_format",
    "get_supported_formats",
]
