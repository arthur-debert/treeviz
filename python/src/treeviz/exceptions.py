"""
3viz Exception Classes

This module contains all custom exception classes used throughout the 3viz library.
Separating exceptions prevents circular import issues between modules.
"""


class ConversionError(Exception):
    """Raised when conversion fails due to malformed data or configuration."""

    pass
