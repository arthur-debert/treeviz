"""
This module provides utility functions for treeviz adapters.
"""

import sys
from typing import Any, Dict, Optional, Tuple, Callable
from functools import wraps


from dataclasses import asdict

from ..definitions.model import AdapterDef
from ..definitions import AdapterLib
from ..formats import DocumentFormatError, load_document as load_doc_file
from ..icon_pack import get_icon_pack, IconPack
from ..const import DEFAULT_ICON_PACK, ICONS
from ..model import Node


def exit_on_error(func: Callable) -> Callable:
    """
    Decorator that catches exceptions, prints a formatted error, and exits.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper


def load_adapter(
    adapter_spec: str | Dict[str, Any] | AdapterDef,
    adapter_format: Optional[str] = None,
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
        from dataclasses import asdict

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
        adapter_dict = load_doc_file(file_path, format_name=adapter_format)

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


def convert_document(
    document: Any, adapter_def: Dict[str, Any]
) -> Optional[Node]:
    """
    Convert a document using a given adapter definition.
    """
    from .core import adapt_node

    return adapt_node(document, adapter_def)


def _find_icon_in_pack(node_type: str, pack: IconPack) -> str | None:
    """Finds an icon for a node_type in a given pack, checking name and
    aliases."""
    for icon_name, icon_def in pack.icons.items():
        if node_type == icon_name or node_type in icon_def.aliases:
            return icon_def.icon
    return None


def resolve_icon(node_type: str, icons_map: dict[str, str]) -> str:
    """
    Resolves an icon for a given node type using the icons map from the
    adapter definition.
    """
    if not node_type:
        return ICONS.get("unknown", "?")

    # 1. Check for a direct mapping for the node_type in icons_map
    icon_ref = icons_map.get(node_type)

    if icon_ref:
        if "." not in icon_ref:
            # It's a direct icon, use as is
            return icon_ref

        # It's a pack reference, e.g., "pack.icon"
        pack_name, icon_name = icon_ref.split(".", 1)
        try:
            pack = get_icon_pack(pack_name)
            if icon_name in pack.icons:
                return pack.icons[icon_name].icon
        except KeyError:
            # Pack not found, fall through to default pack logic for the
            # icon_name
            pass

        # If icon not found in specified pack, try finding `icon_name` in
        # default pack
        default_pack_ref = icons_map.get("") or icons_map.get("*")
        if default_pack_ref:
            try:
                default_pack = get_icon_pack(default_pack_ref)
                if icon_name in default_pack.icons:
                    return default_pack.icons[icon_name].icon
            except KeyError:
                pass  # Default pack not found, fall through

        # Fallback to treeviz pack for the icon_name
        if icon_name in DEFAULT_ICON_PACK.icons:
            return DEFAULT_ICON_PACK.icons[icon_name].icon

    # 2. No direct mapping, check for default pack configured in the
    # adapter
    default_pack_ref = icons_map.get("") or icons_map.get("*")
    if default_pack_ref:
        try:
            pack = get_icon_pack(default_pack_ref)
            icon = _find_icon_in_pack(node_type, pack)
            if icon:
                return icon
        except KeyError:
            # Default pack not found, fall through to treeviz pack
            pass

    # 3. Fallback to the global default "treeviz" icon pack
    icon = _find_icon_in_pack(node_type, DEFAULT_ICON_PACK)
    if icon:
        return icon

    # 4. Final fallback to ICONS mapping (from original implementation)
    return ICONS.get(node_type, ICONS.get("unknown", "?"))
