"""
Path Expression Parser for 3viz Advanced Extraction

This module provides robust path expression parsing using a recursive descent parser.
Supports dot notation, array indexing, and bracket notation.
"""

from typing import Any, Dict, List


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
        raise ValueError("Path expression cannot be empty")

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
        raise ValueError(
            f"Unexpected character '{_current_char(state)}' at position {state['pos']} in path: '{state['path']}'"
        )

    # Ensure we parsed at least one valid step
    if not steps:
        raise ValueError(
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
        raise ValueError(
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
        raise ValueError(f"Unclosed bracket in path: '{state['path']}'")

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
        raise ValueError(
            f"Expected digit at position {state['pos']} in path: '{state['path']}'"
        )

    while state["pos"] < state["length"] and _current_char(state).isdigit():
        state["pos"] += 1

    try:
        return int(state["path"][start : state["pos"]])
    except ValueError:
        raise ValueError(
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
        raise ValueError(
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
        raise ValueError(
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
        raise ValueError(
            f"Expected '{expected}' at position {state['pos']}, got '{_current_char(state)}' in path: '{state['path']}'"
        )
    state["pos"] += 1


def _consume_bracket_close(state: Dict[str, Any]):
    """Consume closing bracket with specific error message for unclosed brackets."""
    if _current_char(state) != "]":
        if state["pos"] >= state["length"]:
            raise ValueError(f"Unclosed bracket in path: '{state['path']}'")
        else:
            raise ValueError(
                f"Expected ']' at position {state['pos']}, got '{_current_char(state)}' in path: '{state['path']}'"
            )
    state["pos"] += 1


def _is_identifier_start(char: str) -> bool:
    """Check if character can start an identifier."""
    return char.isalpha() or char == "_"


def _is_identifier_char(char: str) -> bool:
    """Check if character can be in an identifier."""
    return char.isalnum() or char == "_"
