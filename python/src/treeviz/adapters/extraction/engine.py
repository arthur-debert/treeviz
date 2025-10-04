"""
Main Extraction Engine for 3viz Advanced Extraction

This module orchestrates the complete extraction pipeline including
path evaluation, transformations, filtering, and collection mapping.
"""

import logging
from typing import Any, Dict

from .path_evaluator import extract_by_path
from .transforms import apply_transformation
from .filters import filter_collection

# Set up module logger for debugging extraction pipeline
logger = logging.getLogger(__name__)


def extract_attribute(source_node: Any, extraction_spec: Any) -> Any:
    """
    Extract attribute using enhanced extraction with sophisticated processing pipeline.

    This is the orchestration method that coordinates all Phase 2 features.
    The processing pipeline follows a specific order to ensure consistent behavior:

    Pipeline Order (critical for correct results):
    1. Path extraction (primary → fallback → default)
    2. Transformation (after extraction, before filtering)
    3. Filtering (after transformation, only for collections)

    Args:
        source_node: The source node to extract from
        extraction_spec: Extraction specification (string, dict, or callable)

    Returns:
        Extracted and processed value
    """
    logger.debug(f"Extracting attribute with spec: {extraction_spec}")

    # Backward compatibility: callable extraction functions (Phase 1)
    if callable(extraction_spec):
        return extraction_spec(source_node)

    # Backward compatibility: simple string paths (Phase 1)
    if isinstance(extraction_spec, str):
        try:
            result = extract_by_path(source_node, extraction_spec)
            return result
        except ValueError:
            # If path parsing fails, treat string as literal value
            logger.debug(
                f"Treating '{extraction_spec}' as literal value (not a valid path)"
            )
            return extraction_spec

    # Literal values: constants, numbers, booleans in definition
    if not isinstance(extraction_spec, dict):
        return extraction_spec  # Literal value pass-through

    # ================== PHASE 2 PROCESSING PIPELINE ==================

    # Step 1: Primary path extraction
    primary_value = None
    if "path" in extraction_spec:
        primary_value = extract_by_path(source_node, extraction_spec["path"])

    # Step 2: Fallback path extraction (if primary failed)
    if primary_value is None and "fallback" in extraction_spec:
        logger.debug("Primary path failed, trying fallback")
        primary_value = extract_by_path(
            source_node, extraction_spec["fallback"]
        )

    # Step 3: Default value application (if all extractions failed)
    if primary_value is None and "default" in extraction_spec:
        logger.debug("All paths failed, using default value")
        primary_value = extraction_spec["default"]

    # Step 4: Transformation application (after extraction, before filtering)
    if primary_value is not None and "transform" in extraction_spec:
        primary_value = apply_transformation(
            primary_value, extraction_spec["transform"]
        )

    # Step 5: Collection filtering (after transformation, only for lists)
    if primary_value is not None and "filter" in extraction_spec:
        if isinstance(primary_value, list):
            primary_value = filter_collection(
                primary_value, extraction_spec["filter"]
            )
        else:
            logger.warning(
                f"Cannot filter non-list value: {type(primary_value)}. "
                f"Filtering requires list input, got {type(primary_value).__name__}. "
                f"Check if transformation changed type unexpectedly."
            )

    # Step 6: Collection mapping (after filtering, transforms lists into new structures)
    if primary_value is not None and "map" in extraction_spec:
        if isinstance(primary_value, list):
            primary_value = apply_collection_mapping(
                primary_value, extraction_spec["map"]
            )
        else:
            logger.warning(
                f"Cannot map non-list value: {type(primary_value)}. "
                f"Mapping requires list input, got {type(primary_value).__name__}."
            )

    return primary_value


def apply_collection_mapping(
    collection: list, map_spec: Dict[str, Any]
) -> list:
    """
    Apply collection mapping to transform list items using templates.

    The map_spec should contain:
    - template: dict/object template with placeholders like ${item} or ${variable}
    - variable: name of the variable representing each item (default: "item")

    Example:
        collection = ["a", "b", "c"]
        map_spec = {
            "template": {"t": "ListItem", "c": "${item}"},
            "variable": "item"
        }
        Result: [{"t": "ListItem", "c": "a"}, {"t": "ListItem", "c": "b"}, {"t": "ListItem", "c": "c"}]

    Args:
        collection: List of items to transform
        map_spec: Mapping specification with template and variable name

    Returns:
        List of transformed items

    Raises:
        ValueError: If map_spec is invalid or template substitution fails
    """
    if not isinstance(collection, list):
        raise ValueError(
            f"Collection mapping requires list input, got {type(collection).__name__}"
        )

    if not isinstance(map_spec, dict):
        raise ValueError(
            f"Map specification must be dict, got {type(map_spec).__name__}"
        )

    if "template" not in map_spec:
        raise ValueError("Map specification must include 'template' field")

    template = map_spec["template"]
    variable_name = map_spec.get("variable", "item")

    logger.debug(
        f"Mapping collection of {len(collection)} items using template {template}"
    )

    result = []
    for item in collection:
        try:
            # Create a context for template substitution
            context = {variable_name: item}
            mapped_item = _substitute_template(template, context)
            result.append(mapped_item)
        except Exception as e:
            raise ValueError(
                f"Template substitution failed for item {item}: {e}"
            ) from e

    return result


def _substitute_template(template: Any, context: Dict[str, Any]) -> Any:
    """
    Recursively substitute template placeholders with context values.

    Placeholders have the format ${variable_name}.
    For string templates, placeholders are replaced with string representation.
    For exact placeholder matches, the actual value is used (preserving type).

    Args:
        template: Template object (can be dict, list, string, or other)
        context: Variable context for substitution

    Returns:
        Template with placeholders substituted
    """
    if isinstance(template, dict):
        # Recursively substitute in dict values
        return {
            key: _substitute_template(value, context)
            for key, value in template.items()
        }

    elif isinstance(template, list):
        # Recursively substitute in list items
        return [_substitute_template(item, context) for item in template]

    elif isinstance(template, str):
        # Check for exact placeholder match (preserve original type)
        for var_name, var_value in context.items():
            placeholder = f"${{{var_name}}}"
            if template == placeholder:
                return (
                    var_value  # Return actual value, not string representation
                )

        # Substitute placeholders within strings (convert to string)
        result = template
        for var_name, var_value in context.items():
            placeholder = f"${{{var_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        return result

    else:
        # Return other types as-is (numbers, booleans, None, etc.)
        return template
