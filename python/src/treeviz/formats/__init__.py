"""
Document format parsing for treeviz.

This module provides format-agnostic document parsing that converts
various input formats (JSON, YAML, XML, etc.) into Python objects
that can then be processed by adapters.
"""

from .model import Format, DocumentFormatError
from .parser import (
    parse_document,
    register_format,
    get_supported_formats,
    get_format_by_name,
)

__all__ = [
    "Format",
    "DocumentFormatError",
    "parse_document",
    "register_format",
    "get_supported_formats",
    "get_format_by_name",
]
