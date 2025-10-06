"""
Custom Jinja2 filters for treeviz templates.
"""

from typing import Dict, Any
from jinja2 import Environment


def format_extras(extra_dict: Dict[str, Any], max_length: int = 20) -> str:
    """
    Format a node's extra dict as a display string.

    Args:
        extra_dict: Dictionary of extra attributes
        max_length: Maximum length for the extras string

    Returns:
        Formatted string like "key1=value1 key2=value2"
        Empty string if dict is empty
    """
    if not extra_dict:
        return ""

    # Format as key=value pairs
    pairs = []
    for key, value in extra_dict.items():
        # Convert value to string, handling special cases
        if value is True:
            pairs.append(key)  # Just show key for boolean true
        elif value is False:
            continue  # Skip false values
        elif value is None:
            continue  # Skip None values
        else:
            pairs.append(f"{key}={value}")

    # Join with spaces
    result = " ".join(pairs)

    # Truncate if too long
    if len(result) > max_length:
        result = result[: max_length - 1] + "…"

    return result


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with … if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def ljust(value: str, width: int, fillchar: str = " ") -> str:
    """Left-justify a string in a field of given width."""
    return str(value).ljust(width, fillchar)


def rjust(value: str, width: int, fillchar: str = " ") -> str:
    """Right-justify a string in a field of given width."""
    return str(value).rjust(width, fillchar)


def register_filters(env: Environment) -> None:
    """
    Register custom filters with a Jinja2 environment.

    Args:
        env: Jinja2 environment to add filters to
    """
    env.filters["format_extras"] = format_extras
    env.filters["truncate"] = truncate_text
    env.filters["ljust"] = ljust
    env.filters["rjust"] = rjust
