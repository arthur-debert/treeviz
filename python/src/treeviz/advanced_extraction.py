"""
Advanced Extraction Engine for 3viz Phase 2

This module provides enhanced declarative extraction capabilities including:
- Complex path expressions with dot notation and array access
- Conditional extraction with fallback chains and default values
- Transformation functions for data manipulation
- Advanced filtering with complex predicates

The extraction engine is designed to handle real-world AST complexity while 
maintaining the "fail fast" principle for malformed definitions.

Key Design Principles:
- Declarative over imperative: prefer definition to code
- Fail fast on malformed input but provide helpful error messages
- Extensible: new transformations and predicates can be easily added
- Performance: optimized for typical AST sizes (up to ~100 nodes)

See treeviz.__init__ module docstring for usage examples and API reference.
"""

import re
import logging
from typing import Any, Dict, List, Union, Callable
from .exceptions import ConversionError

# Set up module logger for debugging path resolution and transformation
logger = logging.getLogger(__name__)


def parse_path_expression(path: str) -> List[Dict[str, Any]]:
    """
    Parse path expression into evaluation steps using a robust recursive descent parser.

    Grammar:
        path_expression := [accessor] | part ('.' part)*
        part := identifier (accessor)*
        accessor := '[' (number | quoted_string | unquoted_string) ']'
        identifier := [a-zA-Z_][a-zA-Z0-9_]*
        number := ['-']?[0-9]+
        quoted_string := '"' [^"]* '"' | "'" [^']* "'"
        unquoted_string := [^\\]\\s]+

    Examples:
        "def_.items[0].name" -> [
            {"type": "attribute", "name": "def_"},
            {"type": "attribute", "name": "items"},
            {"type": "index", "index": 0},
            {"type": "attribute", "name": "name"}
        ]
    """
    if not path.strip():
        raise ConversionError("Path expression cannot be empty")

    parser_state = {"path": path, "pos": 0, "length": len(path)}
    return _parse_path_with_state(parser_state)


def _parse_path_with_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse the path expression into a list of evaluation steps."""
    steps = []

    # Handle edge case: path starting with accessor like "[0].name" or "['key'].value"
    if _current_char(state) == "[":
        accessor = _parse_accessor(state)
        steps.append(accessor)
    else:
        # Standard case: identifier followed by optional accessors
        part_steps = _parse_part(state)
        steps.extend(part_steps)

    # Parse remaining parts connected by dots
    while _current_char(state) == ".":
        _consume(state, ".")
        part_steps = _parse_part(state)
        steps.extend(part_steps)

    # Verify we've consumed the entire input
    if state["pos"] < state["length"]:
        raise ConversionError(
            f"Unexpected character '{_current_char(state)}' at position {state['pos']} in path: '{state['path']}'"
        )

    # Ensure we parsed at least one valid step
    if not steps:
        raise ConversionError(
            f"No valid steps found in path expression: '{state['path']}'"
        )

    return steps


def _parse_part(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse a part: identifier followed by zero or more accessors."""
    steps = []

    # Parse identifier
    identifier = _parse_identifier(state)
    steps.append({"type": "attribute", "name": identifier})

    # Parse any accessors (brackets)
    while _current_char(state) == "[":
        accessor = _parse_accessor(state)
        steps.append(accessor)

    return steps


def _parse_identifier(state: Dict[str, Any]) -> str:
    """Parse an identifier: [a-zA-Z_][a-zA-Z0-9_]*"""
    if not _is_identifier_start(_current_char(state)):
        raise ConversionError(
            f"Expected identifier at position {state['pos']}, got '{_current_char(state)}' in path: '{state['path']}'"
        )

    start = state["pos"]
    while state["pos"] < state["length"] and _is_identifier_char(
        _current_char(state)
    ):
        state["pos"] += 1

    return state["path"][start : state["pos"]]


def _parse_accessor(state: Dict[str, Any]) -> Dict[str, Any]:
    """Parse bracket accessor syntax: '[' content ']'"""
    _consume(state, "[")
    _skip_whitespace(state)

    if state["pos"] >= state["length"]:
        raise ConversionError(f"Unclosed bracket in path: '{state['path']}'")

    # Numeric index detection
    if _current_char(state) == "-" or _current_char(state).isdigit():
        number = _parse_number(state)
        _skip_whitespace(state)
        _consume_bracket_close(state)
        return {"type": "index", "index": number}

    # Quoted string detection
    elif _current_char(state) in ["'", '"']:
        string_value = _parse_quoted_string(state)
        _skip_whitespace(state)
        _consume_bracket_close(state)
        return {"type": "key", "key": string_value}

    else:
        # Unquoted string fallback
        string_value = _parse_unquoted_string(state)
        _skip_whitespace(state)
        _consume_bracket_close(state)
        return {"type": "key", "key": string_value}


def _parse_number(state: Dict[str, Any]) -> int:
    """Parse a number: [0-9]+ | '-' [0-9]+"""
    start = state["pos"]

    # Handle negative numbers
    if _current_char(state) == "-":
        state["pos"] += 1

    if not _current_char(state).isdigit():
        raise ConversionError(
            f"Expected digit at position {state['pos']} in path: '{state['path']}'"
        )

    while state["pos"] < state["length"] and _current_char(state).isdigit():
        state["pos"] += 1

    try:
        return int(state["path"][start : state["pos"]])
    except ValueError:
        raise ConversionError(
            f"Invalid number '{state['path'][start:state['pos']]}' at position {start} in path: '{state['path']}'"
        )


def _parse_quoted_string(state: Dict[str, Any]) -> str:
    """Parse a quoted string: '"' [^"]* '"' | "'" [^']* "'" """
    quote_char = _current_char(state)
    state["pos"] += 1  # Skip opening quote

    start = state["pos"]
    while state["pos"] < state["length"] and _current_char(state) != quote_char:
        state["pos"] += 1

    if state["pos"] >= state["length"]:
        raise ConversionError(
            f"Unclosed string starting at position {start-1} in path: '{state['path']}'"
        )

    string_value = state["path"][start : state["pos"]]
    state["pos"] += 1  # Skip closing quote
    return string_value


def _parse_unquoted_string(state: Dict[str, Any]) -> str:
    """Parse an unquoted string (everything until ] or whitespace)."""
    start = state["pos"]
    while state["pos"] < state["length"] and _current_char(state) not in [
        "]",
        " ",
        "\t",
        "\n",
    ]:
        state["pos"] += 1

    if start == state["pos"]:
        raise ConversionError(
            f"Empty key in bracket at position {state['pos']} in path: '{state['path']}'"
        )

    return state["path"][start : state["pos"]]


def _skip_whitespace(state: Dict[str, Any]):
    """Skip whitespace for human-readable bracket notation."""
    while state["pos"] < state["length"] and _current_char(state) in [
        " ",
        "\t",
        "\n",
    ]:
        state["pos"] += 1


def _current_char(state: Dict[str, Any]) -> str:
    """Get current character with safe bounds checking."""
    if state["pos"] >= state["length"]:
        return ""
    return state["path"][state["pos"]]


def _consume(state: Dict[str, Any], expected: str):
    """Consume expected character with precise error reporting."""
    if _current_char(state) != expected:
        raise ConversionError(
            f"Expected '{expected}' at position {state['pos']}, got '{_current_char(state)}' in path: '{state['path']}'"
        )
    state["pos"] += 1


def _consume_bracket_close(state: Dict[str, Any]):
    """Consume closing bracket with specific error message for unclosed brackets."""
    if _current_char(state) != "]":
        if state["pos"] >= state["length"]:
            raise ConversionError(
                f"Unclosed bracket in path: '{state['path']}'"
            )
        else:
            raise ConversionError(
                f"Expected ']' at position {state['pos']}, got '{_current_char(state)}' in path: '{state['path']}'"
            )
    state["pos"] += 1


def _is_identifier_start(char: str) -> bool:
    """Check if character can start an identifier."""
    return char.isalpha() or char == "_"


def _is_identifier_char(char: str) -> bool:
    """Check if character can be in an identifier."""
    return char.isalnum() or char == "_"


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
        ConversionError: If path expression is malformed
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
        # Adapt any path evaluation error to ConversionError for consistent handling
        raise ConversionError(
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
            raise ConversionError(f"Unknown step type: {step_type}")

    except Exception as e:
        # Enhance error context with step position and path information
        raise ConversionError(
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
        raise ConversionError(
            f"Cannot access key '{key}' on non-mapping type {type(obj)}"
        )

    try:
        return obj[key]
    except (KeyError, TypeError):
        # Key doesn't exist - return None for fallback chains
        return None


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
        ConversionError: If transformation fails or is unknown
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
                raise ConversionError(
                    "Transformation dict must include 'name' field"
                )

            # Extract parameters (exclude 'name' field)
            params = {k: v for k, v in transform_spec.items() if k != "name"}
            return _apply_builtin_transformation(
                value, transform_name, **params
            )

        else:
            raise ConversionError(
                f"Invalid transformation specification type: {type(transform_spec)}"
            )

    except Exception as e:
        # Re-raise ConversionError as-is, wrap other exceptions
        if isinstance(e, ConversionError):
            raise
        else:
            raise ConversionError(f"Transformation failed: {e}") from e


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
        raise ConversionError(
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
        raise ConversionError(
            f"upper transformation requires string input, got {type(value).__name__}"
        )
    return value.upper()


def _text_lower(value: Any) -> str:
    """Adapt to lowercase with type checking."""
    if not isinstance(value, str):
        raise ConversionError(
            f"lower transformation requires string input, got {type(value).__name__}"
        )
    return value.lower()


def _text_capitalize(value: Any) -> str:
    """Capitalize with type checking."""
    if not isinstance(value, str):
        raise ConversionError(
            f"capitalize transformation requires string input, got {type(value).__name__}"
        )
    return value.capitalize()


def _text_strip(value: Any) -> str:
    """Strip whitespace with type checking."""
    if not isinstance(value, str):
        raise ConversionError(
            f"strip transformation requires string input, got {type(value).__name__}"
        )
    return value.strip()


# Type-safe numeric transformations
def _numeric_abs(value: Any) -> Union[int, float]:
    """Absolute value with type checking."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConversionError(
            f"abs transformation requires numeric input, got {type(value).__name__}"
        )
    return abs(value)


def _numeric_round(value: Any, digits: int = 0, **kwargs) -> Union[int, float]:
    """Round number with type checking."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConversionError(
            f"round transformation requires numeric input, got {type(value).__name__}"
        )
    return round(value, digits)


def _format_value(value: Any, format_spec: str = "", **kwargs) -> str:
    """Format value with type checking for format spec."""
    if not isinstance(format_spec, str):
        raise ConversionError(
            f"format transformation requires string format_spec, got {type(format_spec).__name__}"
        )
    try:
        return format(value, format_spec)
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"format transformation failed for value {value} with spec '{format_spec}': {e}"
        ) from e


# Type-safe collection transformations
def _collection_length(value: Any) -> int:
    """Get length with type checking."""
    if not hasattr(value, "__len__"):
        raise ConversionError(
            f"length transformation requires object with __len__, got {type(value).__name__}"
        )
    try:
        return len(value)
    except TypeError as e:
        raise ConversionError(
            f"length transformation failed for {type(value).__name__}: {e}"
        ) from e


def _collection_join(value: Any, separator: str = "", **kwargs) -> str:
    """Join collection elements with type checking."""
    if not hasattr(value, "__iter__") or isinstance(value, (str, bytes)):
        raise ConversionError(
            f"join transformation requires iterable (non-string), got {type(value).__name__}"
        )
    if not isinstance(separator, str):
        raise ConversionError(
            f"join transformation requires string separator, got {type(separator).__name__}"
        )
    try:
        return separator.join(str(x) for x in value)
    except TypeError as e:
        raise ConversionError(
            f"join transformation failed for {type(value).__name__}: {e}"
        ) from e


def _collection_first(value: Any) -> Any:
    """Get first element with type checking."""
    if not hasattr(value, "__getitem__") and not hasattr(value, "__iter__"):
        raise ConversionError(
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
        raise ConversionError(
            f"first transformation failed for {type(value).__name__}: {e}"
        ) from e


def _collection_last(value: Any) -> Any:
    """Get last element with type checking."""
    if not hasattr(value, "__getitem__") and not hasattr(value, "__iter__"):
        raise ConversionError(
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
        raise ConversionError(
            f"last transformation failed for {type(value).__name__}: {e}"
        ) from e


# Explicit type conversion transformations
def _convert_to_str(value: Any) -> str:
    """Explicit conversion to string."""
    try:
        return str(value)
    except Exception as e:
        raise ConversionError(
            f"str transformation failed for {type(value).__name__}: {e}"
        ) from e


def _convert_to_int(value: Any) -> int:
    """Explicit conversion to integer with validation."""
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"int transformation failed for value '{value}' of type {type(value).__name__}: {e}"
        ) from e


def _convert_to_float(value: Any) -> float:
    """Explicit conversion to float with validation."""
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise ConversionError(
            f"float transformation failed for value '{value}' of type {type(value).__name__}: {e}"
        ) from e


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
        ConversionError: If filter specification is malformed
    """
    if not isinstance(collection, list):
        raise ConversionError(
            f"Cannot filter non-list type: {type(collection)}"
        )

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
        # Adapt any filtering error to ConversionError
        if isinstance(e, ConversionError):
            raise
        else:
            raise ConversionError(f"Filter evaluation failed: {e}") from e


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
        raise ConversionError(f"Unknown filter operator: {operator}")


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
