"""
Definition library registry for treeviz.

This module provides a registry system for format definitions,
automatically loading core definitions from the lib directory.
"""

import json
import importlib.resources
from pathlib import Path
from typing import Dict
from ..schema import Definition


class Lib:
    """
    Registry for definition libraries.

    Manages loading and caching of format definitions from the lib directory.
    Provides a clean interface for accessing pre-built definitions.
    """

    _registry: Dict[str, Definition] = {}
    _loaded = False

    @classmethod
    def register(cls, name: str, definition_dict: Dict) -> None:
        """
        Register a definition in the library.

        Args:
            name: Format name (e.g., "mdast", "unist")
            definition_dict: Definition dictionary to convert and store

        Raises:
            Standard Python exceptions: KeyError, ValueError, etc. if definition is invalid
        """
        # Merge with defaults and validate - let exceptions bubble up naturally
        default_def = Definition.default()
        merged_def = default_def.merge_with(definition_dict)
        cls._registry[name] = merged_def

    @classmethod
    def get(cls, format_name: str) -> Definition:
        """
        Get a definition from the library.

        Args:
            format_name: Name of the format (e.g., "mdast", "unist", "json")

        Returns:
            Definition object for the format

        Raises:
            KeyError: If format is not found
        """
        # Ensure core libraries are loaded
        if not cls._loaded:
            cls.load_core_libs()

        if format_name not in cls._registry:
            available_formats = list(cls._registry.keys())
            raise KeyError(
                f"Unknown format '{format_name}'. Available formats: {available_formats}. "
                f"To add a new format, place a JSON definition file in the lib/ directory."
            )

        return cls._registry[format_name]

    @classmethod
    def load_core_libs(cls, reload: bool = False) -> None:
        """
        Load core definitions from the lib directory.

        Args:
            reload: If True, reload even if already loaded
        """
        if cls._loaded and not reload:
            return

        if reload:
            cls._registry.clear()

        # Get all JSON files from the lib directory
        lib_files = []
        try:
            # Try to list files in the lib directory
            with importlib.resources.path(
                "treeviz.definitions.lib", ""
            ) as lib_path:
                lib_files = list(lib_path.glob("*.json"))
        except (ImportError, FileNotFoundError):
            # Fallback: try to access files directly
            lib_files = []
            for filename in ["mdast.json", "unist.json"]:
                try:
                    with importlib.resources.open_text(
                        "treeviz.definitions.lib", filename
                    ):
                        lib_files.append(filename)
                except (ImportError, FileNotFoundError):
                    continue

        # Load each JSON file - let JSON decode errors and file errors bubble up
        for file_item in lib_files:
            if isinstance(file_item, Path):
                filename = file_item.name
                format_name = file_item.stem
                with open(file_item, "r") as f:
                    definition_dict = json.load(f)
            else:
                # file_item is a string filename
                filename = file_item
                format_name = filename.replace(".json", "")
                with importlib.resources.open_text(
                    "treeviz.definitions.lib", filename
                ) as f:
                    definition_dict = json.load(f)

            cls.register(format_name, definition_dict)

        cls._loaded = True

    @classmethod
    def list_formats(cls) -> list[str]:
        """
        List all available format names.

        Returns:
            List of available format names including 'json'
        """
        if not cls._loaded:
            cls.load_core_libs()

        formats = list(cls._registry.keys())
        if "json" not in formats:
            formats.append("json")
        return sorted(formats)

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (mainly for testing)."""
        cls._registry.clear()
        cls._loaded = False
