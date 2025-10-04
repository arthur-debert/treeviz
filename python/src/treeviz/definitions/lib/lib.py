"""
AdapterDef library registry for treeviz.

This module provides a registry system for format definitions,
automatically loading core definitions from the lib directory.
"""

import json
import importlib.resources
from pathlib import Path
from typing import Dict, Union
from ..model import AdapterDef

try:
    from ruamel import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class Lib:
    """
    Registry for definition libraries.

    Manages loading and caching of format definitions from the lib directory.
    Provides a clean interface for accessing pre-built definitions.
    """

    _registry: Dict[str, AdapterDef] = {}
    _loaded = False

    @classmethod
    def register(cls, name: str, definition_dict: Dict) -> None:
        """
        Register a definition in the library.

        Args:
            name: Format name (e.g., "mdast", "unist")
            definition_dict: AdapterDef dictionary to convert and store

        Raises:
            Standard Python exceptions: KeyError, ValueError, etc. if definition is invalid
        """
        # Merge with defaults and validate - let exceptions bubble up naturally
        default_def = AdapterDef.default()
        merged_def = default_def.merge_with(definition_dict)
        cls._registry[name] = merged_def

    @classmethod
    def get(cls, format_name: str) -> AdapterDef:
        """
        Get a definition from the library.

        Args:
            format_name: Name of the format (e.g., "mdast", "unist", "json", "3viz")

        Returns:
            AdapterDef object for the format

        Raises:
            KeyError: If format is not found
        """
        # Handle special case for 3viz (default definition)
        if format_name == "3viz":
            return AdapterDef.default()

        # Ensure core libraries are loaded
        if not cls._loaded:
            cls.load_core_libs()

        if format_name not in cls._registry:
            available_formats = list(cls._registry.keys()) + ["3viz"]
            raise KeyError(
                f"Unknown format '{format_name}'. Available formats: {available_formats}. "
                f"To add a new format, place a JSON definition file in the lib/ directory."
            )

        return cls._registry[format_name]

    @classmethod
    def load_definition_file(cls, file_path: Union[str, Path]) -> Dict:
        """
        Load a definition file, supporting both JSON and YAML based on extension.

        Args:
            file_path: Path to the definition file

        Returns:
            Dictionary containing the definition data

        Raises:
            ValueError: If file format is not supported or parsing fails
        """
        file_path = Path(file_path)

        if file_path.suffix.lower() == ".json":
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {file_path}: {e}")
        elif file_path.suffix.lower() in [".yaml", ".yml"]:
            if not HAS_YAML:
                raise ValueError(
                    "YAML support requires 'ruamel.yaml' package. Install with: pip install ruamel.yaml"
                )
            try:
                yml = yaml.YAML(typ="safe", pure=True)
                with open(file_path, "r") as f:
                    return yml.load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {file_path}: {e}")
        else:
            # Try both formats if extension is unknown
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Try JSON first
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass

                # Try YAML if JSON fails
                if HAS_YAML:
                    try:
                        yml = yaml.YAML(typ="safe", pure=True)
                        return yml.load(content)
                    except yaml.YAMLError:
                        pass

                raise ValueError(f"Could not parse {file_path} as JSON or YAML")
            except Exception as e:
                raise ValueError(f"Error reading {file_path}: {e}")

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

        # Get all JSON and YAML files from the lib directory
        lib_files = []
        try:
            # Try to list files in the lib directory
            with importlib.resources.path(
                "treeviz.definitions.lib", ""
            ) as lib_path:
                lib_files = (
                    list(lib_path.glob("*.json"))
                    + list(lib_path.glob("*.yaml"))
                    + list(lib_path.glob("*.yml"))
                )
        except (ImportError, FileNotFoundError):
            # Fallback: try to access files directly
            lib_files = []
            for filename in [
                "mdast.json",
                "unist.json",
                "mdast.yaml",
                "unist.yaml",
            ]:
                try:
                    with importlib.resources.open_text(
                        "treeviz.definitions.lib", filename
                    ):
                        lib_files.append(filename)
                except (ImportError, FileNotFoundError):
                    continue

        # Load each definition file - let decode errors and file errors bubble up
        for file_item in lib_files:
            if isinstance(file_item, Path):
                filename = file_item.name
                format_name = file_item.stem
                definition_dict = cls.load_definition_file(file_item)
            else:
                # file_item is a string filename
                filename = file_item
                format_name = Path(filename).stem
                # For resources, we need to read the content and parse it
                with importlib.resources.open_text(
                    "treeviz.definitions.lib", filename
                ) as f:
                    content = f.read()

                if filename.endswith(".json"):
                    definition_dict = json.loads(content)
                elif filename.endswith((".yaml", ".yml")):
                    if not HAS_YAML:
                        continue  # Skip YAML files if ruamel.yaml not available
                    yml = yaml.YAML(typ="safe", pure=True)
                    definition_dict = yml.load(content)
                else:
                    continue  # Skip unknown file types

            cls.register(format_name, definition_dict)

        cls._loaded = True

    @classmethod
    def list_formats(cls) -> list[str]:
        """
        List all available format names.

        Returns:
            List of available format names including 'json' and '3viz'
        """
        if not cls._loaded:
            cls.load_core_libs()

        formats = list(cls._registry.keys())
        if "json" not in formats:
            formats.append("json")
        if "3viz" not in formats:
            formats.append("3viz")
        return sorted(formats)

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (mainly for testing)."""
        cls._registry.clear()
        cls._loaded = False
