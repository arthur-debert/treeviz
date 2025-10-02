"""
Configuration Management for 3viz

This module handles loading and validating configuration files for the
declarative converter. Supports JSON configuration files with validation
and helpful error messages.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .converter import ConversionError


def load_config(
    config_path: Optional[str] = None, config_dict: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Load and validate a 3viz configuration.

    Args:
        config_path: Path to JSON configuration file
        config_dict: Configuration dictionary (alternative to file)

    Returns:
        Validated configuration dictionary

    Raises:
        ConversionError: If configuration is invalid
    """
    if config_path and config_dict:
        raise ConversionError("Cannot specify both config_path and config_dict")

    if config_path and not config_dict:
        try:
            path = Path(config_path)
            if not path.exists():
                raise ConversionError(
                    f"Configuration file not found: {config_path}"
                )

            with open(path, "r") as f:
                config = json.load(f)

        except json.JSONDecodeError as e:
            raise ConversionError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConversionError(f"Failed to load configuration file: {e}")

    elif config_dict:
        config = config_dict

    else:
        raise ConversionError("Must specify either config_path or config_dict")

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


def create_sample_config() -> Dict[str, Any]:
    """
    Create a sample configuration for reference.

    Returns:
        Sample configuration dictionary
    """
    return {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "children",
        },
        "icon_map": {
            "document": "⧉",
            "paragraph": "¶",
            "list": "☰",
            "listItem": "•",
            "text": "◦",
        },
        "type_overrides": {
            "paragraph": {"label": "content"},
            "text": {"label": "value", "icon": None},
        },
        "ignore_types": ["comment", "whitespace"],
    }


def save_sample_config(path: str) -> None:
    """
    Save a sample configuration to a file.

    Args:
        path: Path where to save the sample configuration

    Raises:
        ConversionError: If file cannot be written
    """
    try:
        config = create_sample_config()
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise ConversionError(f"Failed to save sample configuration: {e}")


# Common pre-built configurations for popular AST formats
BUILTIN_CONFIGS = {
    "mdast": {
        "attributes": {
            "label": "value",
            "type": "type",
            "children": "children",
        },
        "icon_map": {
            "root": "⧉",
            "paragraph": "¶",
            "text": "◦",
            "heading": "⊤",
            "list": "☰",
            "listItem": "•",
        },
        "type_overrides": {
            "paragraph": {
                "label": lambda node: "".join(
                    child.get("value", "") for child in node.get("children", [])
                )
            },
            "heading": {
                "label": lambda node: "".join(
                    child.get("value", "") for child in node.get("children", [])
                )
            },
            "listItem": {
                "label": lambda node: "".join(
                    child.get("value", "") for child in node.get("children", [])
                )
            },
        },
    },
    "json": {
        "attributes": {
            "label": lambda node: (
                str(node)
                if not isinstance(node, (dict, list))
                else type(node).__name__
            ),
            "type": lambda node: type(node).__name__,
            "children": lambda node: (
                list(node.values())
                if isinstance(node, dict)
                else (list(node) if isinstance(node, list) else [])
            ),
        },
        "icon_map": {
            "dict": "{}",
            "list": "[]",
            "str": '"',
            "int": "#",
            "float": "#",
            "bool": "?",
            "NoneType": "∅",
        },
    },
}


def get_builtin_config(format_name: str) -> Dict[str, Any]:
    """
    Get a built-in configuration for a popular format.

    Args:
        format_name: Name of the format ("mdast", "json", etc.)

    Returns:
        Built-in configuration

    Raises:
        ConversionError: If format is not supported
    """
    if format_name not in BUILTIN_CONFIGS:
        available = ", ".join(BUILTIN_CONFIGS.keys())
        raise ConversionError(
            f"Unknown format '{format_name}'. Available: {available}"
        )

    return BUILTIN_CONFIGS[format_name].copy()


def exit_on_config_error(func):
    """Decorator to exit with status 1 on configuration errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConversionError as e:
            print(f"Configuration Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
