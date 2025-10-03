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

from ..adapter import ConversionError
from .schema import Definition


# Deep merge functionality moved to Definition.merge_with() method


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
    def_ = get_default_def().to_dict(merge_icons=False)

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
        default_definition = Definition.from_dict(def_)
        merged_definition = default_definition.merge_with(user_def)
        def_ = merged_definition.to_dict(merge_icons=False)

    # Validate definition
    return validate_def(def_)


def validate_def(def_: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a definition dictionary using the Definition dataclass.

    Args:
        def_: Configuration to validate

    Returns:
        Validated definition dictionary (original format)

    Raises:
        ConversionError: If definition is invalid
    """
    # Use dataclass for validation but return original format for backwards compatibility
    definition = Definition.from_dict(def_)
    return definition.to_dict(merge_icons=False)


def get_default_def() -> Definition:
    """
    Get the default definition.

    Returns:
        Default Definition object with baseline configuration
    """
    return Definition.default()


def load_format_def(format_name: str) -> Definition:
    """
    Load a format-specific definition merged with defaults.

    Args:
        format_name: Name of the format ("mdast", "unist", etc.)

    Returns:
        Definition object merged with defaults

    Raises:
        ConversionError: If format is not supported
    """
    from .lib import Lib

    return Lib.get(format_name)


def exit_on_def_error(func):
    """Decorator to exit with status 1 on definition errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConversionError as e:
            print(f"Configuration Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
