"""
Advanced Extraction Engine for 3viz Phase 2

This module provides enhanced declarative extraction capabilities including:
- Complex path expressions with dot notation and array access
- Conditional extraction with fallback chains and default values
- Transformation functions for data manipulation
- Advanced filtering with complex predicates

The extraction engine is designed to handle real-world AST complexity while 
maintaining the "fail fast" principle for malformed configurations.

Key Design Principles:
- Declarative over imperative: prefer configuration to code
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


class PathParser:
    """
    Robust recursive descent parser for path expressions.

    This parser implements a formal grammar approach to replace the previous fragile
    regex-based parsing. The grammar ensures proper handling of edge cases like
    nested brackets, quoted strings with special characters, and mixed access patterns.

    Why recursive descent? Regex-based parsing fails on nested structures and
    complex quoting scenarios. A formal parser provides:
    - Predictable error messages with exact position information
    - Extensibility for future syntax additions
    - Clear separation of tokenization and evaluation phases
    - Proper handling of edge cases like empty brackets or malformed quotes

    Grammar Definition:
        path_expression := [accessor] | part ('.' part)*
        part := identifier (accessor)*
        accessor := '[' (number | quoted_string | unquoted_string) ']'
        identifier := [a-zA-Z_][a-zA-Z0-9_]*
        number := ['-']?[0-9]+
        quoted_string := '"' [^"]* '"' | "'" [^']* "'"
        unquoted_string := [^\\]\\s]+

    Critical Implementation Notes:
    - Position tracking enables precise error reporting
    - Whitespace is allowed inside brackets for readability
    - Both positive and negative array indices are supported
    - String keys can be quoted or unquoted for flexibility
    - Parser state is immutable - each parse creates a new instance
    """

    def __init__(self, path: str):
        self.path = path
        self.pos = 0
        self.length = len(path)

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse the path expression into a list of evaluation steps.

        Each step represents one access operation and contains:
        - {"type": "attribute", "name": "field_name"} for object.field
        - {"type": "index", "index": 0} for array[0] or array[-1]
        - {"type": "key", "key": "string_key"} for dict['key']

        Returns:
            List of step dictionaries that can be executed sequentially

        Raises:
            ConversionError: For malformed syntax with exact position info
        """
        steps = []

        # Handle edge case: path starting with accessor like "[0].name" or "['key'].value"
        # This supports expressions that immediately index into the root object
        if self.current_char() == "[":
            accessor = self._parse_accessor()
            steps.append(accessor)
        else:
            # Standard case: identifier followed by optional accessors
            # e.g., "config.items[0].name" starts with "config"
            part_steps = self._parse_part()
            steps.extend(part_steps)

        # Parse remaining parts connected by dots
        # Each dot introduces a new attribute access on the previous result
        while self.current_char() == ".":
            self._consume(".")
            part_steps = self._parse_part()
            steps.extend(part_steps)

        # Verify we've consumed the entire input - leftover characters indicate syntax errors
        # This prevents silent acceptance of malformed expressions like "config.item.extra_garbage"
        if self.pos < self.length:
            raise ConversionError(
                f"Unexpected character '{self.current_char()}' at position {self.pos} in path: '{self.path}'"
            )

        # Ensure we parsed at least one valid step - empty paths are meaningless
        if not steps:
            raise ConversionError(
                f"No valid steps found in path expression: '{self.path}'"
            )

        return steps

    def _parse_part(self) -> List[Dict[str, Any]]:
        """Parse a part: identifier followed by zero or more accessors."""
        steps = []

        # Parse identifier
        identifier = self._parse_identifier()
        steps.append({"type": "attribute", "name": identifier})

        # Parse any accessors (brackets)
        while self.current_char() == "[":
            accessor = self._parse_accessor()
            steps.append(accessor)

        return steps

    def _parse_identifier(self) -> str:
        """Parse an identifier: [a-zA-Z_][a-zA-Z0-9_]*"""
        if not self._is_identifier_start(self.current_char()):
            raise ConversionError(
                f"Expected identifier at position {self.pos}, got '{self.current_char()}' in path: '{self.path}'"
            )

        start = self.pos
        while self.pos < self.length and self._is_identifier_char(
            self.current_char()
        ):
            self.pos += 1

        return self.path[start : self.pos]

    def _parse_accessor(self) -> Dict[str, Any]:
        """
        Parse bracket accessor syntax: '[' content ']'

        Supports three content types:
        1. Numbers: [0], [-1], [42] -> {"type": "index", "index": N}
        2. Quoted strings: ["key"], ['complex-key'] -> {"type": "key", "key": "..."}
        3. Unquoted strings: [key] -> {"type": "key", "key": "key"}

        Critical parsing decisions:
        - Numbers are detected by leading digit or minus sign
        - Quoted strings allow any content including spaces and special chars
        - Unquoted strings provide backward compatibility but are limited
        - Whitespace is allowed around content for readability: [ "key" ]
        """
        self._consume("[")

        # Allow whitespace after opening bracket for readability: [ "key" ]
        self._skip_whitespace()

        # Check for premature end - this catches malformed expressions like "config["
        if self.pos >= self.length:
            raise ConversionError(f"Unclosed bracket in path: '{self.path}'")

        # Numeric index detection: starts with digit or minus (for negative indices)
        # This handles: [0], [-1], [42], but not [-invalid] which will fail in _parse_number
        if self.current_char() == "-" or self.current_char().isdigit():
            number = self._parse_number()
            self._skip_whitespace()
            self._consume_bracket_close()
            return {"type": "index", "index": number}

        # Quoted string detection: allows spaces, special chars, reserved words
        # Essential for keys like "complex-key", "spaces in key", "class", etc.
        elif self.current_char() in ["'", '"']:
            string_value = self._parse_quoted_string()
            self._skip_whitespace()
            self._consume_bracket_close()
            return {"type": "key", "key": string_value}

        else:
            # Unquoted string fallback - maintains backward compatibility
            # Limited to simple identifiers without spaces or special characters
            # Used for cases like [key] where quotes were omitted
            string_value = self._parse_unquoted_string()
            self._skip_whitespace()
            self._consume_bracket_close()
            return {"type": "key", "key": string_value}

    def _parse_number(self) -> int:
        """Parse a number: [0-9]+ | '-' [0-9]+"""
        start = self.pos

        # Handle negative numbers
        if self.current_char() == "-":
            self.pos += 1

        if not self.current_char().isdigit():
            raise ConversionError(
                f"Expected digit at position {self.pos} in path: '{self.path}'"
            )

        while self.pos < self.length and self.current_char().isdigit():
            self.pos += 1

        try:
            return int(self.path[start : self.pos])
        except ValueError:
            raise ConversionError(
                f"Invalid number '{self.path[start:self.pos]}' at position {start} in path: '{self.path}'"
            )

    def _parse_quoted_string(self) -> str:
        """Parse a quoted string: '"' [^"]* '"' | "'" [^']* "'" """
        quote_char = self.current_char()
        self.pos += 1  # Skip opening quote

        start = self.pos
        while self.pos < self.length and self.current_char() != quote_char:
            self.pos += 1

        if self.pos >= self.length:
            raise ConversionError(
                f"Unclosed string starting at position {start-1} in path: '{self.path}'"
            )

        string_value = self.path[start : self.pos]
        self.pos += 1  # Skip closing quote
        return string_value

    def _parse_unquoted_string(self) -> str:
        """Parse an unquoted string (everything until ] or whitespace)."""
        start = self.pos
        while self.pos < self.length and self.current_char() not in [
            "]",
            " ",
            "\t",
            "\n",
        ]:
            self.pos += 1

        if start == self.pos:
            raise ConversionError(
                f"Empty key in bracket at position {self.pos} in path: '{self.path}'"
            )

        return self.path[start : self.pos]

    def _skip_whitespace(self):
        """
        Skip whitespace for human-readable bracket notation.

        Allows expressions like [ "key" ] and [ 0 ] instead of requiring
        ["key"] and [0]. This improves readability in complex configurations
        without affecting parsing correctness.

        Only skips ASCII whitespace (space, tab, newline) to avoid issues
        with Unicode whitespace characters that might be part of keys.
        """
        while self.pos < self.length and self.current_char() in [
            " ",
            "\t",
            "\n",
        ]:
            self.pos += 1

    def current_char(self) -> str:
        """
        Get current character with safe bounds checking.

        Returns empty string at end of input instead of raising IndexError.
        This design choice simplifies parser logic by eliminating bounds checks
        in every parsing method. Empty string is falsy and doesn't match any
        expected characters, naturally terminating parsing loops.
        """
        if self.pos >= self.length:
            return ""
        return self.path[self.pos]

    def _consume(self, expected: str):
        """
        Consume expected character with precise error reporting.

        This is a fundamental parsing primitive that advances position only
        when the expected character is found. The detailed error message
        includes position information essential for debugging malformed paths.

        Used throughout the parser for consuming structural characters like
        dots, brackets, and quotes that have syntactic meaning.
        """
        if self.current_char() != expected:
            raise ConversionError(
                f"Expected '{expected}' at position {self.pos}, got '{self.current_char()}' in path: '{self.path}'"
            )
        self.pos += 1

    def _consume_bracket_close(self):
        """Consume closing bracket with specific error message for unclosed brackets."""
        if self.current_char() != "]":
            if self.pos >= self.length:
                raise ConversionError(
                    f"Unclosed bracket in path: '{self.path}'"
                )
            else:
                raise ConversionError(
                    f"Expected ']' at position {self.pos}, got '{self.current_char()}' in path: '{self.path}'"
                )
        self.pos += 1

    def _is_identifier_start(self, char: str) -> bool:
        """Check if character can start an identifier."""
        return char.isalpha() or char == "_"

    def _is_identifier_char(self, char: str) -> bool:
        """Check if character can be in an identifier."""
        return char.isalnum() or char == "_"


class PathExpressionEngine:
    """
    Handles complex path expressions for attribute extraction.

    Supports:
    - Simple attribute access: "name"
    - Dot notation: "metadata.title"
    - Array indexing: "children[0]" or "items[-1]"
    - Complex paths: "config.database.connections[0].host"
    - Bracket notation: "data['complex-key']"

    Error Handling:
    - Returns None for missing paths (allows fallback chains)
    - Raises ConversionError for malformed expressions
    - Logs debug info for path resolution troubleshooting
    """

    def extract_by_path(self, source_node: Any, path_expression: str) -> Any:
        """
        Extract value using complex path expression.

        The path expression is parsed and evaluated step by step, allowing
        for dot notation, array indexing, and bracket notation.

        Args:
            source_node: The source node to extract from
            path_expression: Path like "config.items[0].name"

        Returns:
            Extracted value or None if path doesn't exist

        Raises:
            ConversionError: If path expression is malformed

        Example:
            engine = PathExpressionEngine()

            # Simple dot notation
            value = engine.extract_by_path(node, "metadata.title")

            # Array access with negative indexing
            value = engine.extract_by_path(node, "children[-1].name")

            # Complex nested access
            value = engine.extract_by_path(node, "config.db.connections[0].host")
        """
        logger.debug(
            f"Extracting path '{path_expression}' from {type(source_node)}"
        )

        try:
            # Parse the path expression into individual steps
            steps = self._parse_path_expression(path_expression)

            current = source_node
            for step_index, step in enumerate(steps):
                if current is None:
                    logger.debug(
                        f"Path evaluation stopped at step {step_index}: {step} (current is None)"
                    )
                    return None

                current = self._evaluate_step(
                    current, step, step_index, path_expression
                )

            logger.debug(f"Path '{path_expression}' resolved to: {current}")
            return current

        except Exception as e:
            # Convert any path evaluation error to ConversionError for consistent handling
            raise ConversionError(
                f"Failed to evaluate path expression '{path_expression}': {e}"
            ) from e

    def _parse_path_expression(self, path: str) -> List[Dict[str, Any]]:
        """
        Parse path expression into evaluation steps using a robust recursive descent parser.

        Grammar:
            path_expression := part ('.' part)*
            part := identifier (accessor)*
            accessor := '[' (number | string) ']'
            identifier := [a-zA-Z_][a-zA-Z0-9_]*
            number := [0-9]+ | '-' [0-9]+
            string := '"' [^"]* '"' | "'" [^']* "'"

        Examples:
            "config.items[0].name" -> [
                {"type": "attribute", "name": "config"},
                {"type": "attribute", "name": "items"},
                {"type": "index", "index": 0},
                {"type": "attribute", "name": "name"}
            ]
        """
        if not path.strip():
            raise ConversionError("Path expression cannot be empty")

        parser = PathParser(path)
        return parser.parse()

    def _evaluate_step(
        self,
        current: Any,
        step: Dict[str, Any],
        step_index: int,
        full_path: str,
    ) -> Any:
        """
        Evaluate a single step in the path expression against the current value.

        Each step represents one access operation. The complexity here comes from
        supporting multiple Python data types and access patterns:

        - Attribute access: for objects, namedtuples, modules
        - Dictionary access: for dicts, mappings
        - List/tuple access: for sequences
        - Mixed access: when objects have both dict-like and attribute interfaces

        Critical design decisions:
        1. None propagation: If current is None, return None (allows fallback chains)
        2. Error context: Wrap access errors with step info for debugging
        3. Type flexibility: Same path syntax works on different object types
        4. Graceful failure: Missing attributes return None rather than crashing
        """
        step_type = step["type"]

        try:
            # Dispatch to specialized access methods based on step type
            # Each method handles the complexity of Python's varied access patterns
            if step_type == "attribute":
                return self._get_attribute(current, step["name"])
            elif step_type == "index":
                return self._get_by_index(current, step["index"])
            elif step_type == "key":
                return self._get_by_key(current, step["key"])
            else:
                # This should never happen with correct parser implementation
                raise ConversionError(f"Unknown step type: {step_type}")

        except Exception as e:
            # Enhance error context with step position and path information
            # This is crucial for debugging complex nested path expressions
            raise ConversionError(
                f"Step {step_index} failed in path '{full_path}' at {step}: {e}"
            ) from e

    def _get_attribute(self, obj: Any, attr_name: str) -> Any:
        """
        Get attribute from object, handling Python's complex attribute access patterns.

        The complexity here stems from Python's flexible object model where the same
        syntax (obj.attr) can mean different things depending on the object type.

        Access Strategy (in order of preference):
        1. Dictionary access for dict-like objects (avoids method name conflicts)
        2. Attribute access for regular objects, classes, namedtuples
        3. Return None for missing attributes (enables fallback chains)

        Critical edge cases handled:
        - Dict objects have methods like 'items', 'keys' that shouldn't be accessed via attr_name
        - Namedtuples are dict-like but should use attribute access (have _fields)
        - Callable attributes (methods) are skipped for safety
        - Custom __getitem__ implementations might raise different exception types
        """
        # Strategy 1: Dictionary-style access for dict-like objects
        # This prevents accidentally accessing dict methods like obj.items when attr_name="items"
        # The _fields check excludes namedtuples which should use attribute access
        if hasattr(obj, "__getitem__") and not hasattr(
            obj, "_fields"
        ):  # Not a namedtuple
            try:
                return obj[attr_name]
            except (KeyError, TypeError):
                # KeyError: key doesn't exist in dict
                # TypeError: object doesn't support item assignment (e.g., some custom types)
                pass

        # Strategy 2: Object attribute access for classes, namedtuples, modules, etc.
        # This handles the majority of Python object attribute access
        if hasattr(obj, attr_name):
            attr = getattr(obj, attr_name)
            # Security: Skip callable attributes (methods) to prevent accidental method calls
            # AST nodes typically contain data, not behavior that should be called
            if not callable(attr):
                return attr

        # Strategy 3: Graceful failure - return None to enable fallback chains
        # This allows expressions like path="title" fallback="name" to work seamlessly
        return None

    def _attribute_exists(self, obj: Any, attr_name: str) -> bool:
        """Check if an attribute exists without retrieving its value."""
        # For dict-like objects
        if hasattr(obj, "__getitem__") and not hasattr(obj, "_fields"):
            try:
                return attr_name in obj
            except (TypeError, KeyError):
                pass

        # For object attributes
        if hasattr(obj, attr_name):
            attr = getattr(obj, attr_name)
            return not callable(attr)

        return False

    def _get_by_index(self, obj: Any, index: int) -> Any:
        """Get item by integer index, supporting negative indexing."""
        if not hasattr(obj, "__getitem__"):
            return None  # Return None instead of raising error to support fallback chains

        try:
            return obj[index]
        except (IndexError, TypeError):
            # Index out of bounds or wrong type - return None for fallback chains
            return None

    def _get_by_key(self, obj: Any, key: str) -> Any:
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


class TransformationEngine:
    """
    Applies transformations to extracted values.

    Supports built-in transformations (upper, lower, truncate, etc.) and custom
    transformation functions. Transformations are applied after extraction but
    before fallback chains, allowing for sophisticated data manipulation.

    Built-in Transformations:
    - Text: upper, lower, capitalize, strip, truncate
    - Numeric: abs, round, format
    - Collections: length, join, first, last
    - Custom: user-provided callable functions

    Error Handling:
    - Invalid transformation names raise ConversionError
    - Transformation failures are logged and re-raised
    - Null/None values skip transformation (allows fallback chains)
    """

    def __init__(self):
        """Initialize with built-in transformation functions."""
        # Registry of built-in transformation functions
        # Each function takes (value, **kwargs) and returns transformed value
        self.transformations = {
            # Text transformations - require string-like input
            "upper": self._text_upper,
            "lower": self._text_lower,
            "capitalize": self._text_capitalize,
            "strip": self._text_strip,
            "truncate": self._truncate_text,
            # Numeric transformations - require numeric input
            "abs": self._numeric_abs,
            "round": self._numeric_round,
            "format": self._format_value,
            # Collection transformations - require collection input
            "length": self._collection_length,
            "join": self._collection_join,
            "first": self._collection_first,
            "last": self._collection_last,
            # Type transformations - explicit conversion
            "str": self._convert_to_str,
            "int": self._convert_to_int,
            "float": self._convert_to_float,
        }

    def apply_transformation(
        self, value: Any, transform_spec: Union[str, Dict[str, Any], Callable]
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

        Example:
            engine = TransformationEngine()

            # Simple built-in transformation
            result = engine.apply_transformation("hello", "upper")  # "HELLO"

            # Transformation with parameters
            result = engine.apply_transformation(
                "very long text",
                {"name": "truncate", "max_length": 10}
            )  # "very long…"

            # Custom transformation function
            result = engine.apply_transformation(
                [1, 2, 3],
                lambda items: f"Count: {len(items)}"
            )  # "Count: 3"
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
                if transform_spec not in self.transformations:
                    available = ", ".join(self.transformations.keys())
                    raise ConversionError(
                        f"Unknown transformation '{transform_spec}'. Available: {available}"
                    )

                return self.transformations[transform_spec](value)

            elif isinstance(transform_spec, dict):
                # Transformation with parameters
                transform_name = transform_spec.get("name")
                if not transform_name:
                    raise ConversionError(
                        "Transformation dict must include 'name' field"
                    )

                if transform_name not in self.transformations:
                    available = ", ".join(self.transformations.keys())
                    raise ConversionError(
                        f"Unknown transformation '{transform_name}'. Available: {available}"
                    )

                # Extract parameters (exclude 'name' field)
                params = {
                    k: v for k, v in transform_spec.items() if k != "name"
                }
                return self.transformations[transform_name](value, **params)

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

    def _truncate_text(
        self, value: Any, max_length: int = 50, suffix: str = "…", **kwargs
    ) -> str:
        """
        Truncate text with intelligent suffix handling for AST visualization.

        This transformation addresses a critical UX need: AST nodes often contain
        very long content (entire function bodies, long identifiers) but UI space
        is limited to ~50 characters in typical tree views.

        Algorithm details:
        - Suffix length is reserved from max_length (avoids "text that's..." exceeding limit)
        - Zero/negative available space returns just the suffix (handles edge cases)
        - String conversion handles non-string values (numbers, None, objects)
        - Unicode suffix (…) is preferred over ASCII (...) for compactness

        Common usage: {"transform": {"name": "truncate", "max_length": 30, "suffix": "..."}}
        """
        text = str(value)
        if len(text) <= max_length:
            return text

        # Calculate available space after reserving suffix length
        # This ensures final result never exceeds max_length
        available_length = max_length - len(suffix)
        if available_length <= 0:
            # Edge case: suffix is longer than max_length
            # Return truncated suffix rather than empty string
            return suffix[:max_length] if max_length > 0 else ""

        return text[:available_length] + suffix

    # Type-safe text transformations
    def _text_upper(self, value: Any, **kwargs) -> str:
        """Convert to uppercase with type checking."""
        if not isinstance(value, str):
            raise ConversionError(
                f"upper transformation requires string input, got {type(value).__name__}"
            )
        return value.upper()

    def _text_lower(self, value: Any, **kwargs) -> str:
        """Convert to lowercase with type checking."""
        if not isinstance(value, str):
            raise ConversionError(
                f"lower transformation requires string input, got {type(value).__name__}"
            )
        return value.lower()

    def _text_capitalize(self, value: Any, **kwargs) -> str:
        """Capitalize with type checking."""
        if not isinstance(value, str):
            raise ConversionError(
                f"capitalize transformation requires string input, got {type(value).__name__}"
            )
        return value.capitalize()

    def _text_strip(self, value: Any, **kwargs) -> str:
        """Strip whitespace with type checking."""
        if not isinstance(value, str):
            raise ConversionError(
                f"strip transformation requires string input, got {type(value).__name__}"
            )
        return value.strip()

    # Type-safe numeric transformations
    def _numeric_abs(self, value: Any, **kwargs) -> Union[int, float]:
        """Absolute value with type checking."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConversionError(
                f"abs transformation requires numeric input, got {type(value).__name__}"
            )
        return abs(value)

    def _numeric_round(
        self, value: Any, digits: int = 0, **kwargs
    ) -> Union[int, float]:
        """Round number with type checking."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConversionError(
                f"round transformation requires numeric input, got {type(value).__name__}"
            )
        return round(value, digits)

    def _format_value(self, value: Any, format_spec: str = "", **kwargs) -> str:
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
    def _collection_length(self, value: Any, **kwargs) -> int:
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

    def _collection_join(
        self, value: Any, separator: str = "", **kwargs
    ) -> str:
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

    def _collection_first(self, value: Any, **kwargs) -> Any:
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

    def _collection_last(self, value: Any, **kwargs) -> Any:
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
    def _convert_to_str(self, value: Any, **kwargs) -> str:
        """Explicit conversion to string."""
        try:
            return str(value)
        except Exception as e:
            raise ConversionError(
                f"str transformation failed for {type(value).__name__}: {e}"
            ) from e

    def _convert_to_int(self, value: Any, **kwargs) -> int:
        """Explicit conversion to integer with validation."""
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ConversionError(
                f"int transformation failed for value '{value}' of type {type(value).__name__}: {e}"
            ) from e

    def _convert_to_float(self, value: Any, **kwargs) -> float:
        """Explicit conversion to float with validation."""
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ConversionError(
                f"float transformation failed for value '{value}' of type {type(value).__name__}: {e}"
            ) from e


class FilterEngine:
    """
    Filters collections based on complex predicates.

    Supports various predicate types for filtering children or other collections:
    - Equality: {"field": "value"}
    - Membership: {"field": {"in": [values]}}
    - Pattern matching: {"field": {"matches": "regex"}}
    - Comparison: {"field": {"gt": 10}}
    - Logical: {"and": [predicates]} or {"or": [predicates]}

    The filter engine is optimized for common AST filtering tasks like removing
    comment nodes, filtering by visibility, or selecting specific node types.
    """

    def filter_collection(
        self, collection: List[Any], filter_spec: Dict[str, Any]
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

        Example:
            engine = FilterEngine()

            # Simple equality filter
            items = [{"type": "func"}, {"type": "class"}, {"type": "func"}]
            result = engine.filter_collection(items, {"type": "func"})
            # [{"type": "func"}, {"type": "func"}]

            # Complex predicate with membership test
            result = engine.filter_collection(
                items,
                {"type": {"in": ["func", "class"]}}
            )

            # Logical combination
            result = engine.filter_collection(
                items,
                {"and": [{"type": "func"}, {"name": {"startswith": "get_"}}]}
            )
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
                if self._evaluate_predicate(item, filter_spec)
            ]
            logger.debug(
                f"Filter result: {len(filtered)} items from {len(collection)}"
            )
            return filtered

        except Exception as e:
            # Convert any filtering error to ConversionError
            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(f"Filter evaluation failed: {e}") from e

    def _evaluate_predicate(self, item: Any, predicate: Dict[str, Any]) -> bool:
        """
        Evaluate whether item matches the predicate using recursive boolean logic.

        This is the core of the filtering engine's logic. The complexity arises from
        supporting nested boolean expressions while maintaining performance.

        Predicate Structure:
        - Simple: {"field": "value"} -> equality test
        - Logical: {"and": [pred1, pred2]} -> all must be true
        - Logical: {"or": [pred1, pred2]} -> at least one must be true
        - Negation: {"not": pred} -> invert the result
        - Complex: {"field": {"operator": "value"}} -> operator-based test

        Critical implementation details:
        1. Short-circuit evaluation for performance (all/any are lazy)
        2. Recursive descent for nested logical structures
        3. Field-level evaluation delegates to specialized handlers
        4. Multiple field conditions in one predicate use AND semantics
        """
        # Logical operator handling - these take precedence over field conditions
        # The recursive nature allows arbitrary nesting: {"and": [{"or": [...]}, {...}]}

        if "and" in predicate:
            # Short-circuit AND: stop on first False result for performance
            # This is essential when filtering large collections
            return all(
                self._evaluate_predicate(item, sub_pred)
                for sub_pred in predicate["and"]
            )

        if "or" in predicate:
            # Short-circuit OR: stop on first True result for performance
            # Particularly important for complex predicates with expensive operations
            return any(
                self._evaluate_predicate(item, sub_pred)
                for sub_pred in predicate["or"]
            )

        if "not" in predicate:
            # Logical negation - allows expressing exclusion filters
            # e.g., {"not": {"type": "comment"}} excludes comment nodes
            return not self._evaluate_predicate(item, predicate["not"])

        # Field-based predicate evaluation
        # Multiple fields in one predicate use implicit AND semantics
        # e.g., {"type": "function", "visibility": "public"} requires both conditions
        for field, condition in predicate.items():
            if not self._evaluate_field_condition(item, field, condition):
                return False  # Fail fast on first non-matching field

        return True  # All field conditions passed

    def _evaluate_field_condition(
        self, item: Any, field: str, condition: Any
    ) -> bool:
        """
        Evaluate condition on a specific field, supporting complex path expressions.

        This method bridges path expression complexity with condition evaluation.
        The field parameter can be a simple name or complex path like "config.items[0].name".

        Condition Types:
        1. Simple equality: condition = "value" -> field_value == "value"
        2. Operator-based: condition = {"gt": 10} -> field_value > 10
        3. Multi-operator: condition = {"gt": 5, "lt": 15} -> 5 < field_value < 15

        Performance considerations:
        - Path extraction is cached within this evaluation
        - Simple equality is optimized (no dict iteration)
        - Complex operators fail fast on first non-match
        """
        # Extract field value using path engine - this supports complex expressions
        # like "metadata.config[0].settings" not just simple field names
        # Creating new PathExpressionEngine is lightweight (stateless design)
        path_engine = PathExpressionEngine()
        field_value = path_engine.extract_by_path(item, field)

        # Optimization: Simple equality test (most common case)
        # Avoids dict iteration and operator dispatch for basic comparisons
        if not isinstance(condition, dict):
            return field_value == condition

        # Complex condition with operators - supports multiple operators per field
        # e.g., {"gt": 5, "lt": 15} creates range conditions
        # All operators must pass (implicit AND semantics)
        for operator, expected in condition.items():
            if not self._evaluate_operator(field_value, operator, expected):
                return False  # Fail fast optimization

        return True  # All operators passed

    def _evaluate_operator(
        self, field_value: Any, operator: str, expected: Any
    ) -> bool:
        """
        Evaluate specific operator conditions - the workhorse of complex filtering.

        This method implements the extensive operator vocabulary needed for AST filtering.
        Each operator category serves specific filtering needs:

        Membership: Fast set-based filtering for type lists, visibility sets
        String ops: Essential for name-based filtering (method prefixes, patterns)
        Comparisons: Numeric filtering (line counts, depths, priorities)
        Type checks: Runtime type validation for mixed content

        Performance notes:
        - String conversion is explicit (str()) to handle numeric/None values safely
        - Regex compilation is deferred to Python's re module caching
        - Comparison operators assume comparable types (int, float, string)
        - Type name comparison avoids isinstance() complexity
        """
        # Membership tests - optimized for filtering by type lists, visibility sets
        # Common use: {"type": {"in": ["function", "class"]}} or {"visibility": {"not_in": ["private"]}}
        if operator == "in":
            return field_value in expected
        elif operator == "not_in":
            return field_value not in expected

        # String operations - essential for name-based and content filtering
        # String conversion handles None, numbers, and other types gracefully
        elif operator == "startswith":
            # Common use: {"name": {"startswith": "get_"}} for accessor methods
            return str(field_value).startswith(expected)
        elif operator == "endswith":
            # Common use: {"name": {"endswith": "_test"}} for test functions
            return str(field_value).endswith(expected)
        elif operator == "contains":
            # Common use: {"content": {"contains": "TODO"}} for finding todos
            return expected in str(field_value)
        elif operator == "matches":
            # Pattern matching: {"name": {"matches": r"test_\w+_integration"}}
            # Uses Python's re module caching for compiled regex performance
            return bool(re.search(expected, str(field_value)))

        # Comparison operations - for numeric filtering and ordering
        # Critical for filtering by metrics: line counts, complexity, priority
        elif operator == "eq":
            return field_value == expected
        elif operator == "ne":
            return field_value != expected
        elif operator == "gt":
            # Common use: {"line_count": {"gt": 100}} for large functions
            return field_value > expected
        elif operator == "gte":
            return field_value >= expected
        elif operator == "lt":
            # Common use: {"depth": {"lt": 3}} for shallow nesting
            return field_value < expected
        elif operator == "lte":
            return field_value <= expected

        # Type and null checks - essential for handling mixed AST content
        # These avoid expensive type introspection in favor of simple checks
        elif operator == "is_none":
            # Exact None checking: {"optional_field": {"is_none": True}}
            return field_value is None
        elif operator == "is_not_none":
            # Non-null filtering: {"content": {"is_not_none": True}}
            return field_value is not None
        elif operator == "type":
            # Type filtering: {"value": {"type": "str"}} for string fields
            # Uses __name__ for readable type specification
            return type(field_value).__name__ == expected

        else:
            # Fail fast on unknown operators - prevents silent filter failures
            # This is critical for catching typos in filter configurations
            raise ConversionError(f"Unknown filter operator: {operator}")


class AdvancedAttributeExtractor:
    """
    Enhanced attribute extractor with fallback chains, transformations, and filtering.

    This is the main entry point for Phase 2 enhanced extraction features.
    It orchestrates the path engine, transformation engine, and filter engine
    to provide sophisticated attribute extraction capabilities.

    Configuration Format:
    {
        "path": "basic.path",           # Simple path (Phase 1 compatibility)
        "fallback": "backup.path",      # Fallback if main path fails
        "default": "default_value",     # Default if all paths fail
        "transform": "upper",           # Apply transformation to result
        "filter": {"type": "function"}  # Filter collections (for children)
    }

    The extractor processes these in order: path → transform → filter → fallback → default
    """

    def __init__(self):
        """Initialize with sub-engines for different extraction phases."""
        self.path_engine = PathExpressionEngine()
        self.transform_engine = TransformationEngine()
        self.filter_engine = FilterEngine()

    def extract_attribute(self, source_node: Any, extraction_spec: Any) -> Any:
        """
        Extract attribute using enhanced extraction with sophisticated processing pipeline.

        This is the orchestration method that coordinates all Phase 2 features.
        The processing pipeline follows a specific order to ensure consistent behavior:

        Pipeline Order (critical for correct results):
        1. Path extraction (primary → fallback → default)
        2. Transformation (after extraction, before filtering)
        3. Filtering (after transformation, only for collections)

        Why this order matters:
        - Fallbacks work on raw extracted values (before transformation)
        - Transformations can modify data type (string → dict, list → string)
        - Filtering requires consistent data type (always list)
        - Defaults are applied before transformation (allows transforming defaults)

        Backward Compatibility:
        - String specs → direct path extraction (Phase 1)
        - Callable specs → custom function call (Phase 1)
        - Literal values → pass-through (constants in config)

        Example processing flows:
        1. {"path": "name", "transform": "upper"} → extract → transform → return
        2. {"path": "missing", "fallback": "title", "default": "Untitled"} → extract(fail) → extract(success) → return
        3. {"path": "items", "filter": {"type": "func"}} → extract → filter → return
        """
        logger.debug(f"Extracting attribute with spec: {extraction_spec}")

        # Backward compatibility: callable extraction functions (Phase 1)
        # These bypass the entire pipeline and call user-provided functions directly
        if callable(extraction_spec):
            return extraction_spec(source_node)

        # Backward compatibility: simple string paths (Phase 1)
        # These use only path extraction, no transformation or filtering
        if isinstance(extraction_spec, str):
            result = self.path_engine.extract_by_path(
                source_node, extraction_spec
            )
            return result

        # Literal values: constants, numbers, booleans in configuration
        # These skip all processing and return the value directly
        if not isinstance(extraction_spec, dict):
            return extraction_spec  # Literal value pass-through

        # ================== PHASE 2 PROCESSING PIPELINE ==================

        # Step 1: Primary path extraction
        # This is the main extraction attempt using the specified path
        primary_value = None
        if "path" in extraction_spec:
            primary_value = self.path_engine.extract_by_path(
                source_node, extraction_spec["path"]
            )

        # Step 2: Fallback path extraction (if primary failed)
        # Fallbacks enable robust extraction when data structure varies
        # e.g., path="title" fallback="name" handles nodes with either field
        if primary_value is None and "fallback" in extraction_spec:
            logger.debug("Primary path failed, trying fallback")
            primary_value = self.path_engine.extract_by_path(
                source_node, extraction_spec["fallback"]
            )

        # Step 3: Default value application (if all extractions failed)
        # Defaults ensure extraction always succeeds, preventing None propagation
        if primary_value is None and "default" in extraction_spec:
            logger.debug("All paths failed, using default value")
            primary_value = extraction_spec["default"]

        # Step 4: Transformation application (after extraction, before filtering)
        # Order is critical: transform the extracted value before filtering
        # This allows transformations that change data type (e.g., list → string)
        if primary_value is not None and "transform" in extraction_spec:
            primary_value = self.transform_engine.apply_transformation(
                primary_value, extraction_spec["transform"]
            )

        # Step 5: Collection filtering (after transformation, only for lists)
        # Filtering is always the last step to work on final transformed data
        # Non-list values are skipped with a warning (configuration error detection)
        if primary_value is not None and "filter" in extraction_spec:
            if isinstance(primary_value, list):
                primary_value = self.filter_engine.filter_collection(
                    primary_value, extraction_spec["filter"]
                )
            else:
                logger.warning(
                    f"Cannot filter non-list value: {type(primary_value)}. "
                    f"Filtering requires list input, got {type(primary_value).__name__}. "
                    f"Check if transformation changed type unexpectedly."
                )

        return primary_value

    def _path_exists_in_source(self, source_node: Any, path: str) -> bool:
        """Check if a simple path exists in the source node (for error reporting)."""
        # For simple paths (no dots or brackets), just check if the attribute exists
        if "." not in path and "[" not in path:
            if hasattr(source_node, "__getitem__"):  # Dict-like
                try:
                    return path in source_node
                except (TypeError, KeyError):
                    pass
            return hasattr(source_node, path)

        # For complex paths, this is more complex to check without false positives
        # For now, assume complex paths are intentional and may validly return None
        return True

    def _get_available_attributes(self, source_node: Any) -> str:
        """Get a string listing available attributes for error messages."""
        attrs = []

        # Get dictionary keys if dict-like
        if hasattr(source_node, "__getitem__") and hasattr(source_node, "keys"):
            try:
                attrs.extend(list(source_node.keys()))
            except (TypeError, AttributeError):
                pass

        # Get object attributes if object-like
        if hasattr(source_node, "__dict__"):
            attrs.extend(
                [
                    k
                    for k in source_node.__dict__.keys()
                    if not k.startswith("_")
                ]
            )
        elif hasattr(source_node, "__slots__"):
            attrs.extend(source_node.__slots__)
        else:
            # Try to get non-private attributes via dir()
            try:
                attrs.extend(
                    [
                        k
                        for k in dir(source_node)
                        if not k.startswith("_")
                        and not callable(getattr(source_node, k, None))
                    ]
                )
            except (TypeError, AttributeError):
                pass

        # Remove duplicates and sort
        attrs = sorted(set(attrs))

        if not attrs:
            return "none found"

        return ", ".join(attrs[:10]) + ("..." if len(attrs) > 10 else "")
