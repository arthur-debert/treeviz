"""
Configuration Management for 3viz

This module handles loading and validating configuration files for the
declarative converter. Supports JSON configuration files with validation
and helpful error messages.

## Configuration Format

3viz uses JSON configuration files to define how AST nodes are converted and displayed.
A configuration file contains four main sections:

### Basic Configuration Example

```json
{
  "attributes": {
    "label": "value",
    "type": "type", 
    "children": "children"
  },
  "icon_map": {
    "document": "⧉",
    "paragraph": "¶",
    "text": "◦",
    "heading": "⊤",
    "list": "☰",
    "listItem": "•"
  },
  "type_overrides": {
    "paragraph": {
      "label": "content"
    }
  },
  "ignore_types": ["comment", "whitespace"]
}
```

### Configuration Sections

#### 1. attributes (required)
Maps 3viz node properties to source node attributes:
- `label`: Property containing the text to display
- `type`: Property containing the node type
- `children`: Property containing child nodes

#### 2. icon_map (optional)
Maps node types to display symbols:
```json
{
  "icon_map": {
    "document": "⧉",
    "heading": "⊤", 
    "paragraph": "¶",
    "unknown": "?"
  }
}
```

#### 3. type_overrides (optional)
Overrides attributes for specific node types:
```json
{
  "type_overrides": {
    "text": {
      "label": "textContent",
      "icon": "◦"
    },
    "heading": {
      "label": "title"
    }
  }
}
```

#### 4. ignore_types (optional)
List of node types to skip during conversion:
```json
{
  "ignore_types": ["comment", "whitespace", "position"]
}
```

### Advanced Configuration

For complex attribute extraction, you can specify nested paths:
```json
{
  "attributes": {
    "label": "props.title",
    "type": "node.type",
    "children": "content.children"
  }
}
```

### Built-in Configurations

3viz includes built-in configurations for popular formats:
- `mdast`: Markdown AST format
- `json`: Generic JSON structures

Use them with:
```python
from treeviz.config import get_builtin_config
config = get_builtin_config("mdast")
```

### Configuration Loading

Configurations are loaded and merged with defaults:
1. Default configuration provides base settings
2. User configuration overrides specific values
3. Result includes all necessary fields

```python
from treeviz.config import load_config

# Load from file
config = load_config(config_path="my_config.json")

# Load from dictionary  
config = load_config(config_dict={"icon_map": {"custom": "★"}})

# Use defaults only
config = load_config()
```
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import importlib.resources

from .converter import ConversionError


def _deep_merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge configuration dictionaries, with override taking precedence.
    
    Args:
        base: Base configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_config(result[key], value)
        else:
            result[key] = value
            
    return result


def load_config(
    config_path: Optional[str] = None, config_dict: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Load and validate a 3viz configuration.

    Args:
        config_path: Path to JSON configuration file (optional)
        config_dict: Configuration dictionary (optional, alternative to file)

    Returns:
        Validated configuration dictionary merged with defaults.
        If no config is provided, returns default configuration.

    Raises:
        ConversionError: If configuration is invalid
    """
    # Start with default configuration
    config = get_default_config()
    
    # Load user configuration if provided
    user_config = None
    
    if config_path and config_dict:
        raise ConversionError("Cannot specify both config_path and config_dict")

    if config_path:
        try:
            path = Path(config_path)
            if not path.exists():
                raise ConversionError(
                    f"Configuration file not found: {config_path}"
                )

            with open(path, "r") as f:
                user_config = json.load(f)

        except json.JSONDecodeError as e:
            raise ConversionError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConversionError(f"Failed to load configuration file: {e}")

    elif config_dict:
        user_config = config_dict

    # Merge user config with defaults if provided
    if user_config:
        config = _deep_merge_config(config, user_config)

    # Validate configuration
    return validate_config(config)


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a configuration dictionary.

    Args:
        config: Configuration to validate

    Returns:
        Validated configuration (may include defaults)

    Raises:
        ConversionError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise ConversionError("Configuration must be a dictionary")

    # Check for required sections
    if "attributes" not in config:
        raise ConversionError("Configuration must include 'attributes' section")

    attributes = config["attributes"]
    if not isinstance(attributes, dict):
        raise ConversionError("'attributes' section must be a dictionary")

    if "label" not in attributes:
        raise ConversionError(
            "'attributes' must specify how to extract 'label'"
        )

    # Validate optional sections
    if "icon_map" in config and not isinstance(config["icon_map"], dict):
        raise ConversionError("'icon_map' must be a dictionary")

    if "type_overrides" in config and not isinstance(
        config["type_overrides"], dict
    ):
        raise ConversionError("'type_overrides' must be a dictionary")

    if "ignore_types" in config and not isinstance(
        config["ignore_types"], list
    ):
        raise ConversionError("'ignore_types' must be a list")

    # Validate type_overrides structure
    if "type_overrides" in config:
        for type_name, overrides in config["type_overrides"].items():
            if not isinstance(overrides, dict):
                raise ConversionError(
                    f"Type override for '{type_name}' must be a dictionary"
                )

    return config


def _load_config_file(filename: str) -> Dict[str, Any]:
    """
    Load a configuration file from the configs package.
    
    Args:
        filename: Name of the config file to load
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConversionError: If file cannot be loaded
    """
    try:
        with importlib.resources.open_text('treeviz.configs', filename) as f:
            return json.load(f)
    except Exception as e:
        raise ConversionError(f"Failed to load config file '{filename}': {e}")


def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration.
    
    Returns:
        Default configuration loaded from default.json
    """
    return _load_config_file('default.json')






def get_builtin_config(format_name: str) -> Dict[str, Any]:
    """
    Get a built-in configuration for a popular format.

    Args:
        format_name: Name of the format ("mdast", "json", etc.)

    Returns:
        Built-in configuration merged with defaults

    Raises:
        ConversionError: If format is not supported
    """
    # Load config from file
    config = _load_config_file(f'{format_name}.json')
    
    # Merge with default configuration
    default_config = get_default_config()
    merged_config = _deep_merge_config(default_config, config)
    
    return merged_config


def exit_on_config_error(func):
    """Decorator to exit with status 1 on configuration errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConversionError as e:
            print(f"Configuration Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
