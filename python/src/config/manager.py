"""
Centralized configuration management system.

"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Type, Union

from ruamel.yaml import YAML


class FileLoader(Protocol):
    """Protocol for loading configuration files."""

    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        ...

    def is_file(self, path: Path) -> bool:
        """Check if a path is a file."""
        ...

    def list_directory(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        ...

    def load_file(self, path: Path) -> Dict[str, Any]:
        """Load a configuration file."""
        ...


class DefaultFileLoader:
    """Default file loader using actual filesystem."""

    def __init__(self):
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def list_directory(self, path: Path) -> List[Path]:
        if not path.exists():
            return []
        return list(path.iterdir())

    def load_file(self, path: Path) -> Dict[str, Any]:
        """Load a single configuration file."""
        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif path.suffix.lower() in (".yaml", ".yml"):
            with open(path, "r", encoding="utf-8") as f:
                return self._yaml.load(f)
        else:
            raise ConfigError(
                message=f"Unsupported file type: {path.suffix}",
                spec_name="unknown",
                file_path=path,
            )


@dataclass
class ConfigSpec:
    """Specification for a configuration type."""

    name: str
    pattern: str  # e.g., "themes/*.yaml", "view.yaml"
    collection: bool = False  # True for multiple files, False for single
    merge: bool = True  # For non-collections, merge configs in hierarchy
    dataclass: Optional[Type] = None  # Auto-instantiate to this class
    validator: Optional[Callable[[Dict[str, Any]], bool]] = None
    callback: Optional[Callable[[Any], None]] = None  # Post-process hook

    def matches(self, path: str) -> bool:
        """
        Check if a path matches this spec's pattern.

        Args:
            path: Relative path within the search directory (e.g., "test.yaml" or "adapters/custom.yaml")

        Returns:
            True if the path matches the pattern
        """
        from fnmatch import fnmatch

        return fnmatch(path, self.pattern)


@dataclass
class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""

    message: str
    spec_name: str
    file_path: Optional[Path] = None
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        parts = [f"Config '{self.spec_name}': {self.message}"]
        if self.file_path:
            parts.append(f" in {self.file_path}")
        if self.cause:
            parts.append(f" ({type(self.cause).__name__}: {self.cause})")
        return "".join(parts)


class ConfigManager:
    """
    Centralized configuration management.

    The core design features:
    - Follows XDG Base Directory spec for config file locations
    - Supports multiple config types with flexible patterns
    - Can merge configs from multiple locations
    - Dependency injected for easy and thorough testing

    The core flow:
    1. Register a config spec with name, pattern, dataclass, validator, etc.
    2. Call get(name) to load and cache the configuration
    3. Configs are loaded from multiple locations in order of precedence
    4. Config files can be YAML or JSON

    Example usage:
        manager = ConfigManager(app_name="3viz")

        # Register settings, where values are moerged from
        # multiple possible locations
        manager.register(ConfigSpec(
            name="settings",
            pattern="settings/*.yaml",
            collection=False,
            dataclass=Settings,
            validator=validate_seeting,
        ))


        # These are plugins, instead of being merged, all found files are loaded
        # and returned as a list
        manager.register(ConfigSpec(
            name="plugins",
            pattern="plugins/*.yaml",
            collection=True,
            dataclass=Plugin,
            validator=add_plugin,
        ))

        # Load configurations
        settings = manager.get("settings")
        plugins = manager.get("plugins")

    Provides a unified API for loading, merging, and managing configuration
    files across multiple locations following the XDG Base Directory spec.

    Config search order (later overrides earlier):
    1. Built-in defaults (lowest priority)
    2. User configuration (XDG or home fallback)
    3. Project-local configuration (highest priority)
    4. Explicit paths if provided (for testing)

    Data is merged recursively for single configs, but lists are replaced.


    Future enhancements:
    - Support additional file formats (TOML, INI)
    - Configureable locations
    - Environment variable overrides
    - Command-line overrides
    - Allow no dataclass (in which case it should return a dict)
    - Pre-fetch : load all configs at once
    """

    def __init__(
        self,
        app_name: str = "3viz",
        search_paths: Optional[List[Path]] = None,
        file_loader: Optional[FileLoader] = None,
    ):
        """
        Initialize the configuration manager.

        Args:
            app_name: Application name for config directories
            search_paths: Optional explicit search paths (for testing)
            file_loader: Optional file loader for dependency injection
        """
        self.app_name = app_name
        self._explicit_paths = search_paths
        self.specs: Dict[str, ConfigSpec] = {}
        self._cache: Dict[str, Any] = {}
        self._loader = file_loader or DefaultFileLoader()

    @property
    def search_paths(self) -> List[Path]:
        """Return config search paths in priority order."""
        if self._explicit_paths is not None:
            return self._explicit_paths

        paths = []

        # Order of precedence (later overrides earlier):
        # 1. Built-in defaults (lowest priority)
        pkg_dir = Path(__file__).parent.parent / "treeviz" / "config"
        if self._loader.exists(pkg_dir):
            paths.append(pkg_dir)

        # 2. User configuration (XDG or home fallback)
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / self.app_name
        else:
            config_dir = Path.home() / ".config" / self.app_name

        if self._loader.exists(config_dir):
            paths.append(config_dir)
        else:
            # Fallback to home directory if XDG doesn't exist
            home_config = Path.home() / f".{self.app_name}"
            if self._loader.exists(home_config):
                paths.append(home_config)

        # 3. Project-local configuration (highest priority)
        cwd_config = Path.cwd() / f".{self.app_name}"
        if self._loader.exists(cwd_config):
            paths.append(cwd_config)

        return paths

    def register(self, spec: ConfigSpec) -> None:
        """Register a configuration specification."""
        if spec.name in self.specs:
            raise ValueError(f"Config '{spec.name}' already registered")
        self.specs[spec.name] = spec

    def get(
        self,
        name: str,
        force_reload: bool = False,
        params: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Get configuration by name.

        Args:
            name: Configuration name as registered
            force_reload: Force reload from disk
            params: Optional parameters to format the pattern (e.g., {"name": "default"})

        Returns:
            Loaded configuration (dataclass instance, dict, or list)

        Raises:
            ValueError: If config name not registered
            ConfigError: If loading or validation fails
        """
        # Create cache key that includes params
        cache_key = name
        if params:
            cache_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(params.items()))}"

        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]

        spec = self.specs.get(name)
        if not spec:
            raise ValueError(f"Unknown config: {name}")

        # Create a copy of the spec with formatted pattern if params provided
        if params:
            spec = self._create_parameterized_spec(spec, params)

        try:
            result = self._load_config(spec)
            self._cache[cache_key] = result
            return result
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(
                message="Failed to load configuration", spec_name=name, cause=e
            )

    def clear_cache(self, name: Optional[str] = None) -> None:
        """Clear cached configurations."""
        if name:
            # Clear all cache entries that start with this name
            keys_to_remove = [
                k for k in self._cache if k == name or k.startswith(f"{name}:")
            ]
            for key in keys_to_remove:
                self._cache.pop(key, None)
        else:
            self._cache.clear()

    def _create_parameterized_spec(
        self, spec: ConfigSpec, params: Dict[str, str]
    ) -> ConfigSpec:
        """Create a copy of the spec with formatted pattern."""
        from dataclasses import replace

        formatted_pattern = spec.pattern.format(**params)
        return replace(spec, pattern=formatted_pattern)

    def _load_config(self, spec: ConfigSpec) -> Any:
        """Load configuration according to spec."""
        if spec.collection:
            return self._load_collection(spec)
        else:
            return self._load_single(spec)

    def _load_collection(self, spec: ConfigSpec) -> List[Any]:
        """Load a collection of config files."""
        all_items = []

        for search_dir in self.search_paths:
            items = self._load_from_directory(search_dir, spec)
            all_items.extend(items)

        # Convert to dataclass if specified
        if spec.dataclass and all_items:
            converted_items = []
            for item in all_items:
                try:
                    if hasattr(spec.dataclass, "from_dict"):
                        converted = spec.dataclass.from_dict(item)
                    else:
                        converted = spec.dataclass(**item)
                    converted_items.append(converted)
                except Exception as e:
                    raise ConfigError(
                        message=f"Failed to create {spec.dataclass.__name__}",
                        spec_name=spec.name,
                        cause=e,
                    )
            all_items = converted_items

        # Apply callback if provided
        if spec.callback and all_items:
            spec.callback(all_items)

        return all_items

    def _load_single(self, spec: ConfigSpec) -> Any:
        """Load a single config file with hierarchical merging."""
        merged_data = {}

        # Load in order so later paths override earlier
        for search_dir in self.search_paths:
            data = self._load_from_directory(search_dir, spec, single=True)
            if data:
                if spec.merge:
                    merged_data = self._deep_merge(merged_data, data)
                else:
                    merged_data = data

        if not merged_data and not spec.collection:
            # Return empty dict for single configs if nothing found
            merged_data = {}

        # Validate if validator provided
        if spec.validator and merged_data:
            try:
                if not spec.validator(merged_data):
                    raise ConfigError(
                        message="Validation failed", spec_name=spec.name
                    )
            except Exception as e:
                if isinstance(e, ConfigError):
                    raise
                raise ConfigError(
                    message="Validation error", spec_name=spec.name, cause=e
                )

        # Convert to dataclass if specified
        if spec.dataclass and merged_data:
            try:
                if hasattr(spec.dataclass, "from_dict"):
                    result = spec.dataclass.from_dict(merged_data)
                else:
                    result = spec.dataclass(**merged_data)
            except Exception as e:
                raise ConfigError(
                    message=f"Failed to create {spec.dataclass.__name__}",
                    spec_name=spec.name,
                    cause=e,
                )
        else:
            result = merged_data

        # Apply callback if provided
        if spec.callback and result:
            spec.callback(result)

        return result

    def _load_from_directory(
        self, directory: Path, spec: ConfigSpec, single: bool = False
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """Load config files from a directory matching the spec pattern."""
        # Handle directory prefix in pattern
        if "/" in spec.pattern:
            dir_part, file_part = spec.pattern.rsplit("/", 1)
            search_dir = directory / dir_part
        else:
            search_dir = directory

        if not self._loader.exists(search_dir):
            return [] if not single else None

        results = []

        # Find matching files
        for file_path in self._loader.list_directory(search_dir):
            if self._loader.is_file(file_path):
                # Calculate relative path from the base directory for matching
                try:
                    if "/" in spec.pattern:
                        # For patterns with directories, use relative path from base
                        relative_path = file_path.relative_to(directory)
                        match_path = str(relative_path).replace("\\", "/")
                    else:
                        # For simple patterns, just use filename
                        match_path = file_path.name
                except ValueError:
                    # Path is not relative to directory
                    continue

                if spec.matches(match_path):
                    try:
                        data = self._loader.load_file(file_path)
                        # For adapter configs, inject filename as name if not present
                        if spec.name == "adapters" and "name" not in data:
                            data["name"] = file_path.stem
                        if single:
                            return data
                        results.append(data)
                    except Exception as e:
                        raise ConfigError(
                            message="Failed to load file",
                            spec_name=spec.name,
                            file_path=file_path,
                            cause=e,
                        )

        return results if not single else None

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
