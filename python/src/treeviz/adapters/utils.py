"""
Utility functions for the adapter system.
"""

import sys
from typing import Callable, Tuple, Dict, Any, Optional
from dataclasses import asdict

from ..definitions import AdapterLib, AdapterDef
from ..formats import load_document, DocumentFormatError


def exit_on_error(func: Callable) -> Callable:
    """
    Decorator to exit with status 1 on any exception.

    This implements the "fail fast" principle - any error
    should immediately exit the program with a clear error message.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper


def load_adapter(
    adapter_spec, adapter_format: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Load adapter definition and icons from name, file, or object.

    Args:
        adapter_spec: Adapter name (e.g., "mdast", "3viz"), file path, dict, or AdapterDef object
        adapter_format: Optional format for file-based adapters (json/yaml)
                       If None, auto-detects from file extension

    Returns:
        Tuple of (adapter_definition_dict, icons_dict)

    Raises:
        ValueError: If adapter name not found or file doesn't exist
        DocumentFormatError: If adapter file parsing fails
        TypeError: If adapter_spec is not a supported type
    """
    # Handle different input types
    if isinstance(adapter_spec, dict):
        # Dictionary object - process directly
        return _load_adapter_from_dict(adapter_spec)
    elif hasattr(adapter_spec, "__dict__") and hasattr(adapter_spec, "icons"):
        # AdapterDef object (or similar) - convert to dict
        adapter_dict = (
            asdict(adapter_spec)
            if hasattr(adapter_spec, "__dict__")
            else adapter_spec.__dict__
        )
        return _load_adapter_from_dict(adapter_dict)
    elif isinstance(adapter_spec, str):
        # String - could be name or file path
        # Check if it's a file path (contains path separators or has extension)
        if "/" in adapter_spec or "\\" in adapter_spec or "." in adapter_spec:
            # File-based adapter
            return _load_adapter_from_file(adapter_spec, adapter_format)
        else:
            # Built-in adapter by name
            return _load_adapter_by_name(adapter_spec)
    else:
        raise TypeError(
            f"adapter_spec must be string, dict, or AdapterDef object, got {type(adapter_spec)}"
        )


def _load_adapter_by_name(
    adapter_name: str,
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Load adapter by name (built-in or user-defined)."""
    try:
        if adapter_name == "3viz":
            # Use default 3viz definition
            definition = AdapterDef.default()
        else:
            # Get from library (includes both built-in and user-defined)
            definition = AdapterLib.get(adapter_name)
    except Exception as e:
        available_formats = ["3viz"] + AdapterLib.list_formats()
        raise ValueError(
            f"Unknown adapter '{adapter_name}'. "
            f"Available adapters: {', '.join(available_formats)}"
        ) from e

    # Convert to dict and extract icons
    definition_dict = asdict(definition)
    icons_dict = definition.icons.copy()

    return definition_dict, icons_dict


def _load_adapter_from_file(
    file_path: str, adapter_format: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Load adapter from file path."""
    try:
        # Load the adapter definition file
        adapter_dict = load_document(file_path, format_name=adapter_format)

        if not isinstance(adapter_dict, dict):
            raise ValueError(
                f"Adapter file must contain a dictionary, got {type(adapter_dict).__name__}"
            )

        # Create AdapterDef from the loaded dict to validate and apply defaults
        definition = AdapterDef.from_dict(adapter_dict)

        # Convert back to dict and extract icons
        definition_dict = asdict(definition)
        icons_dict = definition.icons.copy()

        return definition_dict, icons_dict

    except FileNotFoundError:
        raise ValueError(f"Adapter file not found: {file_path}")
    except DocumentFormatError as e:
        raise DocumentFormatError(
            f"Failed to parse adapter file '{file_path}': {str(e)}"
        ) from e
    except Exception as e:
        raise ValueError(
            f"Invalid adapter definition in '{file_path}': {str(e)}"
        ) from e


def _load_adapter_from_dict(
    adapter_dict: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Load adapter from dictionary object."""
    try:
        if not isinstance(adapter_dict, dict):
            raise ValueError(
                f"Adapter dict must be a dictionary, got {type(adapter_dict).__name__}"
            )

        # Create AdapterDef from the dict to validate and apply defaults
        definition = AdapterDef.from_dict(adapter_dict)

        # Convert back to dict and extract icons
        definition_dict = asdict(definition)
        icons_dict = definition.icons.copy()

        return definition_dict, icons_dict

    except Exception as e:
        raise ValueError(f"Invalid adapter definition: {str(e)}") from e


def convert_document(document: Any, adapter_def: Dict[str, Any]) -> Any:
    """
    Convert a document to 3viz Node format using adapter definition.

    Args:
        document: The parsed document (usually dict or list)
        adapter_def: Adapter definition dictionary

    Returns:
        3viz Node object

    Raises:
        Standard Python exceptions from adapt_node (TypeError, KeyError, ValueError, etc.)
    """
    from .core import adapt_node

    return adapt_node(document, adapter_def)
