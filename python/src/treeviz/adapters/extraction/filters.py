"""
Collection Filtering Engine for 3viz Advanced Extraction

This module provides sophisticated collection filtering with support for
complex predicates, boolean logic, and field-based conditions.
"""

import re
import logging
from typing import Any, Dict, List

from .path_evaluator import extract_by_path

# Set up module logger for debugging filtering
logger = logging.getLogger(__name__)


def filter_collection(
    collection: List[Any], filter_spec: Dict[str, Any]
) -> List[Any]:
    """
    Filter collection based on predicate specification.

    Args:
        collection: List of items to filter
        filter_spec: Predicate specification dict

    Returns:
        Filtered list containing only items matching the predicate

    Raises:
        ValueError: If filter specification is malformed
    """
    if not isinstance(collection, list):
        raise ValueError(f"Cannot filter non-list type: {type(collection)}")

    logger.debug(
        f"Filtering collection of {len(collection)} items with spec: {filter_spec}"
    )

    try:
        filtered = [
            item
            for item in collection
            if _evaluate_predicate(item, filter_spec)
        ]
        logger.debug(
            f"Filter result: {len(filtered)} items from {len(collection)}"
        )
        return filtered

    except Exception as e:
        # Adapt any filtering error to ValueError
        if isinstance(e, ValueError):
            raise
        else:
            raise ValueError(f"Filter evaluation failed: {e}") from e


def _evaluate_predicate(item: Any, predicate: Dict[str, Any]) -> bool:
    """Evaluate whether item matches the predicate using recursive boolean logic."""
    # Logical operator handling
    if "and" in predicate:
        return all(
            _evaluate_predicate(item, sub_pred) for sub_pred in predicate["and"]
        )

    if "or" in predicate:
        return any(
            _evaluate_predicate(item, sub_pred) for sub_pred in predicate["or"]
        )

    if "not" in predicate:
        return not _evaluate_predicate(item, predicate["not"])

    # Field-based predicate evaluation
    for field, condition in predicate.items():
        if not _evaluate_field_condition(item, field, condition):
            return False  # Fail fast on first non-matching field

    return True  # All field conditions passed


def _evaluate_field_condition(item: Any, field: str, condition: Any) -> bool:
    """Evaluate condition on a specific field, supporting complex path expressions."""
    field_value = extract_by_path(item, field)

    # Optimization: Simple equality test (most common case)
    if not isinstance(condition, dict):
        return field_value == condition

    # Complex condition with operators
    for operator, expected in condition.items():
        if not _evaluate_operator(field_value, operator, expected):
            return False  # Fail fast optimization

    return True  # All operators passed


def _evaluate_operator(field_value: Any, operator: str, expected: Any) -> bool:
    """Evaluate specific operator conditions."""
    # Membership tests
    if operator == "in":
        return field_value in expected
    elif operator == "not_in":
        return field_value not in expected

    # String operations
    elif operator == "startswith":
        return str(field_value).startswith(expected)
    elif operator == "endswith":
        return str(field_value).endswith(expected)
    elif operator == "contains":
        return expected in str(field_value)
    elif operator == "matches":
        return bool(re.search(expected, str(field_value)))

    # Comparison operations
    elif operator == "eq":
        return field_value == expected
    elif operator == "ne":
        return field_value != expected
    elif operator == "gt":
        return field_value > expected
    elif operator == "gte":
        return field_value >= expected
    elif operator == "lt":
        return field_value < expected
    elif operator == "lte":
        return field_value <= expected

    # Type and null checks
    elif operator == "is_none":
        return field_value is None
    elif operator == "is_not_none":
        return field_value is not None
    elif operator == "type":
        return type(field_value).__name__ == expected

    else:
        raise ValueError(f"Unknown filter operator: {operator}")
