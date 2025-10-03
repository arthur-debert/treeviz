"""
Configuration Management for 3viz

This module handles loading and validating definition files for the
declarative converter. Supports JSON definition files with validation
and helpful error messages.

## Configuration Format

3viz uses JSON definition files to define how AST nodes are converted and displayed.
A definition file contains four main sections:

### Configuration Sections

#### 1. attributes (required)
Maps 3viz node properties to source node attributes:
- `label`: Property containing the text to display
- `type`: Property containing the node type  
- `children`: Property containing child nodes

#### 2. icons (optional)
Maps node types to display symbols using Unicode characters

#### 3. type_overrides (optional)
Overrides attributes for specific node types, allowing per-type customization

#### 4. ignore_types (optional)
List of node types to skip during conversion

### Configuration Files

See the actual definition files for examples:
- `treeviz/definitions/mdast.json` - Markdown AST format
- `treeviz/definitions/unist.json` - Universal Syntax Tree format

### Advanced Configuration

For complex attribute extraction, you can specify nested paths like:
- `"label": "props.title"` - Access nested properties
- `"type": "node.type"` - Deep object access
- `"children": "content.children"` - Nested arrays

### Built-in Configurations

3viz includes built-in definitions for popular formats loaded from files.
Use them with:
```python
from treeviz.definitions import get_builtin_def
def_ = get_builtin_def("mdast")
```

### Configuration Loading

Configurations are loaded and merged with defaults:
1. Default definition provides base settings
2. User definition overrides specific values  
3. Result includes all necessary fields

```python
from treeviz.definitions import load_def

# Load from file
def_ = load_def(def_path="my_def.json")

# Load from dictionary
def_ = load_def(def_dict={"icons": {"custom": "★"}})

# Use defaults only
def_ = load_def()
```
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import importlib.resources

from ..adapter import ConversionError
from ..const import ICONS


def _deep_merge_def(
    base: Dict[str, Any], override: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep merge definition dictionaries, with override taking precedence.

    Args:
        base: Base definition
        override: Override definition
    Returns:
        Merged definition
    """
    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge_def(result[key], value)
        else:
            result[key] = value
    return result


def load_def(
    def_path: Optional[str] = None, def_dict: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Load and validate a 3viz definition.

    Args:
        def_path: Path to JSON definition file (optional)
        def_dict: Configuration dictionary (optional, alternative to file)

    Returns:
        Validated definition dictionary merged with defaults.
        If no def_ is provided, returns default definition.

    Raises:
        ConversionError: If definition is invalid
    """
    # Start with default definition
    def_ = get_default_def()

    # Load user definition if provided
    user_def = None
    if def_path and def_dict:
        raise ConversionError("Cannot specify both def_path and def_dict")

    if def_path:
        try:
            path = Path(def_path)
            if not path.exists():
                raise ConversionError(
                    f"Configuration file not found: {def_path}"
                )

            with open(path, "r") as f:
                user_def = json.load(f)

        except json.JSONDecodeError as e:
            raise ConversionError(f"Invalid JSON in definition file: {e}")
        except Exception as e:
            raise ConversionError(f"Failed to load definition file: {e}")

    elif def_dict:
        user_def = def_dict

    # Merge user def_ with defaults if provided
    if user_def:
        def_ = _deep_merge_def(def_, user_def)

    # Validate definition
    return validate_def(def_)


def validate_def(def_: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a definition dictionary.

    Args:
        def_: Configuration to validate

    Returns:
        Validated definition (may include defaults)

    Raises:
        ConversionError: If definition is invalid
    """
    if not isinstance(def_, dict):
        raise ConversionError("Configuration must be a dictionary")

    # Check for required sections
    if "attributes" not in def_:
        raise ConversionError("Configuration must include 'attributes' section")

    attributes = def_["attributes"]
    if not isinstance(attributes, dict):
        raise ConversionError("'attributes' section must be a dictionary")

    if "label" not in attributes:
        raise ConversionError(
            "'attributes' must specify how to extract 'label'"
        )

    # Validate optional sections
    if "icons" in def_ and not isinstance(def_["icons"], dict):
        raise ConversionError("'icons' must be a dictionary")

    if "type_overrides" in def_ and not isinstance(
        def_["type_overrides"], dict
    ):
        raise ConversionError("'type_overrides' must be a dictionary")

    if "ignore_types" in def_ and not isinstance(def_["ignore_types"], list):
        raise ConversionError("'ignore_types' must be a list")

    # Validate type_overrides structure
    if "type_overrides" in def_:
        for type_name, overrides in def_["type_overrides"].items():
            if not isinstance(overrides, dict):
                raise ConversionError(
                    f"Type override for '{type_name}' must be a dictionary"
                )

    return def_


def _load_def_file(filename: str) -> Dict[str, Any]:
    """
    Load a definition file from the configs package.

    Args:
        filename: Name of the def_ file to load

    Returns:
        Configuration dictionary
    Raises:
        ConversionError: If file cannot be loaded
    """
    try:
        with importlib.resources.open_text(
            "treeviz.definitions", filename
        ) as f:
            return json.load(f)
    except Exception as e:
        raise ConversionError(f"Failed to load def_ file '{filename}': {e}")


def get_default_def() -> Dict[str, Any]:
    """
    Get the default definition.

    Returns:
        Default definition with baseline icons from const.py
    """
    return {
        "attributes": {
            "label": "label",
            "type": "type",
            "children": "children",
        },
        "icons": ICONS.copy(),
        "type_overrides": {},
        "ignore_types": [],
    }


def get_builtin_def(format_name: str) -> Dict[str, Any]:
    """
    Get a built-in definition for a popular format.

    Args:
        format_name: Name of the format ("mdast", "unist", etc.)

    Returns:
        Built-in definition merged with defaults

    Raises:
        ConversionError: If format is not supported
    """
    # Handle special case for generic structures - no special definition needed
    if format_name == "json":
        # JSON/dict structures work automatically with baseline icons from const.py
        return get_default_def()

    # Load def_ from file
    def_ = _load_def_file(f"{format_name}.json")

    # Merge with default definition
    default_def = get_default_def()
    merged_def = _deep_merge_def(default_def, def_)
    return merged_def


def exit_on_def_error(func):
    """Decorator to exit with status 1 on definition errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConversionError as e:
            print(f"Configuration Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
