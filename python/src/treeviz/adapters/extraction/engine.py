"""
Main Extraction Engine for 3viz Advanced Extraction

This module orchestrates the complete extraction pipeline including
path evaluation, transformations, and filtering.
"""

import logging
from typing import Any

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
        result = extract_by_path(source_node, extraction_spec)
        return result

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

    return primary_value
