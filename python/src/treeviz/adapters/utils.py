"""
This module provides utility functions for treeviz adapters.
"""
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Callable
from functools import wraps

from ..definitions.model import AdapterDef
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
    adapter_spec: str | Dict[str, Any] | AdapterDef, adapter_format: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Load an adapter definition from a file, built-in name, dict, or AdapterDef object.
    """
    if isinstance(adapter_spec, AdapterDef):
        adapter_def_dict = adapter_spec.to_dict()
    elif isinstance(adapter_spec, dict):
        adapter_def_dict = adapter_spec
    elif isinstance(adapter_spec, str) and (Path(adapter_spec).suffix in [".json", ".yaml", ".yml"] or Path(adapter_spec).is_file()):
        if not Path(adapter_spec).exists():
            raise ValueError(f"Adapter file not found: {adapter_spec}")
        try:
            adapter_def_dict = load_doc_file(adapter_spec, format_name=adapter_format)
        except DocumentFormatError as e:
            raise DocumentFormatError(f"Failed to parse adapter file: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load adapter file: {e}") from e
    elif isinstance(adapter_spec, str):
        try:
            from ..data import BUILTIN_ADAPTERS
            if adapter_spec not in BUILTIN_ADAPTERS:
                raise KeyError
            adapter_def_dict = BUILTIN_ADAPTERS[adapter_spec]
        except (ImportError, KeyError):
            raise ValueError(f"Unknown adapter '{adapter_spec}'")
    else:
        raise TypeError(f"adapter_spec must be a str, dict, or AdapterDef, not {type(adapter_spec).__name__}")

    if not isinstance(adapter_def_dict, dict):
        raise ValueError("Adapter definition must contain a dictionary.")

    if not any(k in adapter_def_dict for k in ["label", "type", "children"]):
        if 'label' not in adapter_def_dict:
             raise ValueError("Invalid adapter definition: must contain at least a 'label' field.")

    processed_def = AdapterDef.from_dict(adapter_def_dict)

    adapter_dict = processed_def.__dict__
    # asdict is not recursive, so we need to convert the children selector manually
    if isinstance(adapter_dict['children'], AdapterDef):
        adapter_dict['children'] = adapter_dict['children'].to_dict()

    icons_dict = adapter_dict.get("icons", {}).copy()

    return adapter_dict, icons_dict


def convert_document(document: Any, adapter_def: Dict[str, Any]) -> Optional[Node]:
    """
    Convert a document using a given adapter definition.
    """
    from .core import adapt_node
    return adapt_node(document, adapter_def)

def _find_icon_in_pack(node_type: str, pack: IconPack) -> str | None:
    """Finds an icon for a node_type in a given pack, checking name and aliases."""
    for icon_name, icon_def in pack.icons.items():
        if node_type == icon_name or node_type in icon_def.aliases:
            return icon_def.icon
    return None

def resolve_icon(node_type: str, icons_map: dict[str, str]) -> str:
    """
    Resolves an icon for a given node type using the icons map from the adapter definition.
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
            # Pack not found, fall through to default pack logic for the icon_name
            pass

        # If icon not found in specified pack, try finding `icon_name` in default pack
        default_pack_ref = icons_map.get("") or icons_map.get("*")
        if default_pack_ref:
            try:
                default_pack = get_icon_pack(default_pack_ref)
                if icon_name in default_pack.icons:
                    return default_pack.icons[icon_name].icon
            except KeyError:
                pass # Default pack not found, fall through

        # Fallback to 3viz pack for the icon_name
        if icon_name in DEFAULT_ICON_PACK.icons:
            return DEFAULT_ICON_PACK.icons[icon_name].icon

    # 2. No direct mapping, check for default pack configured in the adapter
    default_pack_ref = icons_map.get("") or icons_map.get("*")
    if default_pack_ref:
        try:
            pack = get_icon_pack(default_pack_ref)
            icon = _find_icon_in_pack(node_type, pack)
            if icon:
                return icon
        except KeyError:
            # Default pack not found, fall through to 3viz pack
            pass

    # 3. Fallback to the global default "3viz" icon pack
    icon = _find_icon_in_pack(node_type, DEFAULT_ICON_PACK)
    if icon:
        return icon

    # 4. Final fallback to ICONS mapping (from original implementation)
    return ICONS.get(node_type, ICONS.get("unknown", "?"))