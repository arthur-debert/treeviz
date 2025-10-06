"""
AdapterDef library registry for treeviz.

This module provides a registry system for format definitions,
using the new ConfigLoaders system.
"""

from typing import Dict, List
from .model import AdapterDef
from ..config.loaders import create_config_loaders


class AdapterLib:
    """
    Registry for definition libraries using the new configuration system.
    """

    _loaders = None
    _cache: Dict[str, AdapterDef] = {}

    @classmethod
    def _ensure_loaders(cls):
        """Ensure config loaders are initialized."""
        if cls._loaders is None:
            cls._loaders = create_config_loaders()

    @classmethod
    def get(cls, format_name: str) -> AdapterDef:
        """
        Get a definition from the library.

        Args:
            format_name: Name of the format (e.g., "mdast", "unist", "pandoc", "3viz")

        Returns:
            AdapterDef object for the format

        Raises:
            KeyError: If format is not found
        """
        cls._ensure_loaders()

        # Handle special case for 3viz (default definition)
        if format_name == "3viz":
            return AdapterDef.default()

        # Check cache first
        if format_name in cls._cache:
            return cls._cache[format_name]

        # Try to load the adapter
        adapter = cls._loaders.load_adapter(format_name)
        if adapter:
            cls._cache[format_name] = adapter
            return adapter

        # Not found - provide helpful error
        available = cls.list_formats()
        raise KeyError(
            f"Unknown format '{format_name}'. Available formats: {available}. "
            f"To add a new format, place a YAML definition file in config/adapters/ directory."
        )

    @classmethod
    def list_formats(cls) -> List[str]:
        """
        List all available format names.

        Returns:
            List of format names (including '3viz')
        """
        cls._ensure_loaders()
        formats = ["3viz"]  # Always include default
        formats.extend(cls._loaders.get_adapter_names())
        return sorted(list(set(formats)))

    @classmethod
    def ensure_all_loaded(cls):
        """
        Ensure all definitions are loaded.

        This is a no-op in the new system as adapters are loaded on demand.
        """
        cls._ensure_loaders()

    @classmethod
    def clear_cache(cls):
        """Clear the adapter cache."""
        cls._cache.clear()

    @classmethod
    def clear(cls):
        """Clear the adapter cache and reset loaders. Alias for clear_cache()."""
        cls._cache.clear()
        cls._loaders = None
