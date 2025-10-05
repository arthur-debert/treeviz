"""
Icon resolution for the rendering system.

This module handles icon resolution from RenderingOptions,
replacing the previous adapter-based icon system.
"""

from typing import Optional
from ..icon_pack import get_icon_pack, IconPack
from ..const import ICONS, DEFAULT_ICON_PACK
from .options import RenderingOptions


def resolve_icon_from_options(node_type: str, options: RenderingOptions) -> str:
    """
    Resolve an icon for a given node type using rendering options.

    Resolution order:
    1. Direct icon mapping in options.icons
    2. Icon pack specified in options.icon_pack
    3. Default treeviz icon pack
    4. Fallback to ICONS constant

    Args:
        node_type: The type of node to get an icon for
        options: RenderingOptions containing icon configuration

    Returns:
        Unicode icon character
    """
    if not node_type:
        return ICONS.get("unknown", "?")

    # 1. Check direct icon mapping first
    if node_type in options.icons:
        return options.icons[node_type]

    # 2. Try icon pack if specified
    if options.icon_pack and options.icon_pack != "treeviz":
        try:
            if isinstance(options.icon_pack, str):
                # Icon pack name
                pack = get_icon_pack(options.icon_pack)
                icon = _find_icon_in_pack(node_type, pack)
                if icon:
                    return icon
            elif isinstance(options.icon_pack, dict):
                # Inline icon pack definition
                # TODO: Support inline icon pack definitions
                pass
        except KeyError:
            # Icon pack not found, fall through
            pass

    # 3. Try default treeviz pack
    icon = _find_icon_in_pack(node_type, DEFAULT_ICON_PACK)
    if icon:
        return icon

    # 4. Final fallback to ICONS constant
    return ICONS.get(node_type, ICONS.get("unknown", "?"))


def _find_icon_in_pack(node_type: str, pack: IconPack) -> Optional[str]:
    """Find an icon for a node_type in a given pack, checking name and aliases."""
    for icon_name, icon_def in pack.icons.items():
        if node_type == icon_name or node_type in icon_def.aliases:
            return icon_def.icon
    return None


def get_icon_map_from_options(options: RenderingOptions) -> dict[str, str]:
    """
    Build a complete icon map from rendering options.

    This is useful for compatibility with existing code that expects
    a dictionary of icons.

    Args:
        options: RenderingOptions containing icon configuration

    Returns:
        Dictionary mapping node types to icon characters
    """
    icon_map = {}

    # Start with icon pack icons
    if options.icon_pack:
        try:
            if isinstance(options.icon_pack, str):
                if options.icon_pack == "treeviz":
                    # Use default pack
                    for name, icon_def in DEFAULT_ICON_PACK.icons.items():
                        icon_map[name] = icon_def.icon
                else:
                    # Load specified pack
                    pack = get_icon_pack(options.icon_pack)
                    for name, icon_def in pack.icons.items():
                        icon_map[name] = icon_def.icon
        except KeyError:
            # Pack not found, use defaults
            for name, icon_def in DEFAULT_ICON_PACK.icons.items():
                icon_map[name] = icon_def.icon

    # Override with direct icon mappings
    icon_map.update(options.icons)

    # Add fallback icons from ICONS constant
    for key, value in ICONS.items():
        if key not in icon_map:
            icon_map[key] = value

    return icon_map
