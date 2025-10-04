"""
Transformation Engine for 3viz Advanced Extraction

This module provides data transformation capabilities including text, numeric,
and collection transformations with type safety and error handling.
"""

import logging
from typing import Any, Union, Callable, Dict

# Set up module logger for debugging transformations
logger = logging.getLogger(__name__)


def apply_transformation(
    value: Any, transform_spec: Union[str, Dict[str, Any], Callable]
) -> Any:
    """
    Apply transformation to value based on specification.

    The transform_spec can be:
    - String: name of built-in transformation
    - Dict: transformation with parameters {"name": "truncate", "max_length": 50}
    - Callable: custom transformation function

    Args:
        value: Value to transform
        transform_spec: Transformation specification

    Returns:
        Transformed value

    Raises:
        ValueError: If transformation fails or is unknown
    """
    # Skip transformation for None values (allows fallback chains)
    if value is None:
        return None

    logger.debug(f"Applying transformation {transform_spec} to {value}")

    try:
        if callable(transform_spec):
            # Custom transformation function
            return transform_spec(value)

        elif isinstance(transform_spec, str):
            # Simple built-in transformation name
            return _apply_builtin_transformation(value, transform_spec)

        elif isinstance(transform_spec, dict):
            # Transformation with parameters
            transform_name = transform_spec.get("name")
            if not transform_name:
                raise ValueError(
                    "Transformation dict must include 'name' field"
                )

            # Extract parameters (exclude 'name' field)
            params = {k: v for k, v in transform_spec.items() if k != "name"}
            return _apply_builtin_transformation(
                value, transform_name, **params
            )

        else:
            raise ValueError(
                f"Invalid transformation specification type: {type(transform_spec)}"
            )

    except Exception as e:
        # Re-raise ValueError as-is, wrap other exceptions
        if isinstance(e, ValueError):
            raise
        else:
            raise ValueError(f"Transformation failed: {e}") from e


def _apply_builtin_transformation(value: Any, name: str, **kwargs) -> Any:
    """Apply built-in transformation by name."""
    transformations = {
        # Text transformations
        "upper": lambda v, **k: _text_upper(v),
        "lower": lambda v, **k: _text_lower(v),
        "capitalize": lambda v, **k: _text_capitalize(v),
        "strip": lambda v, **k: _text_strip(v),
        "truncate": lambda v, **k: _truncate_text(v, **k),
        # Numeric transformations
        "abs": lambda v, **k: _numeric_abs(v),
        "round": lambda v, **k: _numeric_round(v, **k),
        "format": lambda v, **k: _format_value(v, **k),
        # Collection transformations
        "length": lambda v, **k: _collection_length(v),
        "join": lambda v, **k: _collection_join(v, **k),
        "first": lambda v, **k: _collection_first(v),
        "last": lambda v, **k: _collection_last(v),
        # Type transformations
        "str": lambda v, **k: _convert_to_str(v),
        "int": lambda v, **k: _convert_to_int(v),
        "float": lambda v, **k: _convert_to_float(v),
    }

    if name not in transformations:
        available = ", ".join(transformations.keys())
        raise ValueError(
            f"Unknown transformation '{name}'. Available: {available}"
        )

    return transformations[name](value, **kwargs)


def _truncate_text(
    value: Any, max_length: int = 50, suffix: str = "…", **kwargs
) -> str:
    """Truncate text with intelligent suffix handling for AST visualization."""
    text = str(value)
    if len(text) <= max_length:
        return text

    # Calculate available space after reserving suffix length
    available_length = max_length - len(suffix)
    if available_length <= 0:
        return suffix[:max_length] if max_length > 0 else ""

    return text[:available_length] + suffix


# Type-safe text transformations
def _text_upper(value: Any) -> str:
    """Adapt to uppercase with type checking."""
    if not isinstance(value, str):
        raise ValueError(
            f"upper transformation requires string input, got {type(value).__name__}"
        )
    return value.upper()


def _text_lower(value: Any) -> str:
    """Adapt to lowercase with type checking."""
    if not isinstance(value, str):
        raise ValueError(
            f"lower transformation requires string input, got {type(value).__name__}"
        )
    return value.lower()


def _text_capitalize(value: Any) -> str:
    """Capitalize with type checking."""
    if not isinstance(value, str):
        raise ValueError(
            f"capitalize transformation requires string input, got {type(value).__name__}"
        )
    return value.capitalize()


def _text_strip(value: Any) -> str:
    """Strip whitespace with type checking."""
    if not isinstance(value, str):
        raise ValueError(
            f"strip transformation requires string input, got {type(value).__name__}"
        )
    return value.strip()


# Type-safe numeric transformations
def _numeric_abs(value: Any) -> Union[int, float]:
    """Absolute value with type checking."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(
            f"abs transformation requires numeric input, got {type(value).__name__}"
        )
    return abs(value)


def _numeric_round(value: Any, digits: int = 0, **kwargs) -> Union[int, float]:
    """Round number with type checking."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(
            f"round transformation requires numeric input, got {type(value).__name__}"
        )
    return round(value, digits)


def _format_value(value: Any, format_spec: str = "", **kwargs) -> str:
    """Format value with type checking for format spec."""
    if not isinstance(format_spec, str):
        raise ValueError(
            f"format transformation requires string format_spec, got {type(format_spec).__name__}"
        )
    try:
        return format(value, format_spec)
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"format transformation failed for value {value} with spec '{format_spec}': {e}"
        ) from e


# Type-safe collection transformations
def _collection_length(value: Any) -> int:
    """Get length with type checking."""
    if not hasattr(value, "__len__"):
        raise ValueError(
            f"length transformation requires object with __len__, got {type(value).__name__}"
        )
    try:
        return len(value)
    except TypeError as e:
        raise ValueError(
            f"length transformation failed for {type(value).__name__}: {e}"
        ) from e


def _collection_join(value: Any, separator: str = "", **kwargs) -> str:
    """Join collection elements with type checking."""
    if not hasattr(value, "__iter__") or isinstance(value, (str, bytes)):
        raise ValueError(
            f"join transformation requires iterable (non-string), got {type(value).__name__}"
        )
    if not isinstance(separator, str):
        raise ValueError(
            f"join transformation requires string separator, got {type(separator).__name__}"
        )
    try:
        return separator.join(str(x) for x in value)
    except TypeError as e:
        raise ValueError(
            f"join transformation failed for {type(value).__name__}: {e}"
        ) from e


def _collection_first(value: Any) -> Any:
    """Get first element with type checking."""
    if not hasattr(value, "__getitem__") and not hasattr(value, "__iter__"):
        raise ValueError(
            f"first transformation requires indexable or iterable, got {type(value).__name__}"
        )
    try:
        if hasattr(value, "__getitem__"):
            # Prefer indexing for lists, tuples, etc.
            return value[0] if len(value) > 0 else None
        else:
            # Fall back to iterator for other iterables
            return next(iter(value), None)
    except (IndexError, TypeError) as e:
        raise ValueError(
            f"first transformation failed for {type(value).__name__}: {e}"
        ) from e


def _collection_last(value: Any) -> Any:
    """Get last element with type checking."""
    if not hasattr(value, "__getitem__") and not hasattr(value, "__iter__"):
        raise ValueError(
            f"last transformation requires indexable or iterable, got {type(value).__name__}"
        )
    try:
        if hasattr(value, "__getitem__"):
            # Prefer indexing for lists, tuples, etc.
            return value[-1] if len(value) > 0 else None
        else:
            # Fall back to iterator for other iterables
            last_item = None
            for item in value:
                last_item = item
            return last_item
    except (IndexError, TypeError) as e:
        raise ValueError(
            f"last transformation failed for {type(value).__name__}: {e}"
        ) from e


# Explicit type conversion transformations
def _convert_to_str(value: Any) -> str:
    """Explicit conversion to string."""
    try:
        return str(value)
    except Exception as e:
        raise ValueError(
            f"str transformation failed for {type(value).__name__}: {e}"
        ) from e


def _convert_to_int(value: Any) -> int:
    """Explicit conversion to integer with validation."""
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"int transformation failed for value '{value}' of type {type(value).__name__}: {e}"
        ) from e


def _convert_to_float(value: Any) -> float:
    """Explicit conversion to float with validation."""
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"float transformation failed for value '{value}' of type {type(value).__name__}: {e}"
        ) from e
