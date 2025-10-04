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

    def __post_init__(self):
        """Validate icon pack after initialization."""
        if not self.name.isidentifier():
            raise ValueError(
                f"Icon pack name '{self.name}' must be a valid Python "
                "identifier."
            )

        for icon_name in self.icons.keys():
            if not icon_name.isidentifier():
                raise ValueError(
                    f"Icon name '{icon_name}' must be a valid Python "
                    "identifier."
                )


_ICON_PACK_REGISTRY: Dict[str, IconPack] = {}


def register_icon_pack(icon_pack: IconPack):
    """
    Registers an icon pack in the global registry.
    """
    _ICON_PACK_REGISTRY[icon_pack.name] = icon_pack


def get_icon_pack(name: str) -> IconPack:
    """
    Retrieves an icon pack from the registry.
    """
    if name not in _ICON_PACK_REGISTRY:
        raise KeyError(f"Icon pack '{name}' not found.")
    return _ICON_PACK_REGISTRY[name]


def list_icon_packs() -> List[str]:
    """
    Returns a list of all registered icon pack names.
    """
    return list(_ICON_PACK_REGISTRY.keys())
