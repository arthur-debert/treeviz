"""
Icon pack management for treeviz.
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Icon:
    """
    Represents a single icon in an icon pack.
    """
    icon: str
    aliases: List[str] = field(default_factory=list)


@dataclass
class IconPack:
    """
    Represents a collection of icons.
    """
    name: str
    icons: Dict[str, Icon]


_ICON_PACK_REGISTRY: Dict[str, IconPack] = {}


def register_icon_pack(icon_pack: IconPack):
    """
    Registers an icon pack in the global registry.
    """
    if "." in icon_pack.name:
        raise ValueError("Icon pack name cannot contain a dot.")
    _ICON_PACK_REGISTRY[icon_pack.name] = icon_pack


def get_icon_pack(name: str) -> IconPack:
    """
    Retrieves an icon pack from the registry.
    """
    if name not in _ICON_PACK_REGISTRY:
        raise KeyError(f"Icon pack '{name}' not found.")
    return _ICON_PACK_REGISTRY[name]