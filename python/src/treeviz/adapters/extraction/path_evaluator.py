"""
Path Evaluation Engine for 3viz Advanced Extraction

This module evaluates parsed path expressions against source objects,
handling dot notation, array indexing, and bracket notation.
"""

import logging
from typing import Any, Dict

from .path_parser import parse_path_expression

# Set up module logger for debugging path resolution
logger = logging.getLogger(__name__)


def extract_by_path(source_node: Any, path_expression: str) -> Any:
    """
    Extract value using complex path expression.

    The path expression is parsed and evaluated step by step, allowing
    for dot notation, array indexing, and bracket notation.

    Args:
        source_node: The source node to extract from
        path_expression: Path like "def_.items[0].name"

    Returns:
        Extracted value or None if path doesn't exist

    Raises:
        ValueError: If path expression is malformed
    """
    logger.debug(
        f"Extracting path '{path_expression}' from {type(source_node)}"
    )

    try:
        # Parse the path expression into individual steps
        steps = parse_path_expression(path_expression)

        current = source_node
        for step_index, step in enumerate(steps):
            if current is None:
                logger.debug(
                    f"Path evaluation stopped at step {step_index}: {step} (current is None)"
                )
                return None

            current = _evaluate_step(current, step, step_index, path_expression)

        logger.debug(f"Path '{path_expression}' resolved to: {current}")
        return current

    except Exception as e:
        # Adapt any path evaluation error to ValueError for consistent handling
        raise ValueError(
            f"Failed to evaluate path expression '{path_expression}': {e}"
        ) from e


def _evaluate_step(
    current: Any, step: Dict[str, Any], step_index: int, full_path: str
) -> Any:
    """Evaluate a single step in the path expression against the current value."""
    step_type = step["type"]

    try:
        # Dispatch to specialized access methods based on step type
        if step_type == "attribute":
            return _get_attribute(current, step["name"])
        elif step_type == "index":
            return _get_by_index(current, step["index"])
        elif step_type == "key":
            return _get_by_key(current, step["key"])
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    except Exception as e:
        # Enhance error context with step position and path information
        raise ValueError(
            f"Step {step_index} failed in path '{full_path}' at {step}: {e}"
        ) from e


def _get_attribute(obj: Any, attr_name: str) -> Any:
    """Get attribute from object, handling Python's complex attribute access patterns."""
    # Strategy 1: Dictionary-style access for dict-like objects
    if hasattr(obj, "__getitem__") and not hasattr(
        obj, "_fields"
    ):  # Not a namedtuple
        try:
            return obj[attr_name]
        except (KeyError, TypeError):
            pass

    # Strategy 2: Object attribute access for classes, namedtuples, modules, etc.
    if hasattr(obj, attr_name):
        attr = getattr(obj, attr_name)
        # Security: Skip callable attributes (methods) to prevent accidental method calls
        if not callable(attr):
            return attr

    # Strategy 3: Graceful failure - return None to enable fallback chains
    return None


def _get_by_index(obj: Any, index: int) -> Any:
    """Get item by integer index, supporting negative indexing."""
    if not hasattr(obj, "__getitem__"):
        return None  # Return None instead of raising error to support fallback chains

    try:
        return obj[index]
    except (IndexError, TypeError):
        # Index out of bounds or wrong type - return None for fallback chains
        return None


def _get_by_key(obj: Any, key: str) -> Any:
    """Get item by string key for dictionary-like objects."""
    if not hasattr(obj, "__getitem__"):
        raise ValueError(
            f"Cannot access key '{key}' on non-mapping type {type(obj)}"
        )

    try:
        return obj[key]
    except (KeyError, TypeError):
        # Key doesn't exist - return None for fallback chains
        return None
