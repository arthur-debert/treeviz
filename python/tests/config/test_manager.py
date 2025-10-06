"""Tests for the configuration manager."""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from clier.config import ConfigManager, ConfigSpec, ConfigError


class MockFileLoader:
    """Mock file loader for testing."""

    def __init__(self, filesystem: Dict[str, Any] = None):
        """
        Initialize with a mock filesystem.

        Uses a flat dictionary structure where:
        - Keys are full file paths as strings
        - Values are file contents (dicts)
        - Directories are represented by having files under them

        Example:
            {
                "/app/config/test.yaml": {"name": "default"},
                "/home/user/.config/3viz/test.yaml": {"name": "user"},
                "/project/.3viz/adapters/custom.yaml": {"name": "custom"}
            }
        """
        self.filesystem = filesystem or {}
        # Build directory set from file paths
        self._directories = set()
        for file_path in self.filesystem.keys():
            # Add all parent directories
            parts = file_path.strip("/").split("/")
            for i in range(1, len(parts)):
                dir_path = "/" + "/".join(parts[:i])
                self._directories.add(dir_path)

    def exists(self, path: Path) -> bool:
        """Check if path exists in mock filesystem."""
        path_str = str(path)
        # Check if it's a file or directory
        return path_str in self.filesystem or path_str in self._directories

    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        return str(path) in self.filesystem

    def list_directory(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        path_str = str(path).rstrip("/")

        if path_str not in self._directories:
            return []

        # Find all direct children
        children = set()
        prefix = path_str + "/"

        for file_path in self.filesystem:
            if file_path.startswith(prefix):
                # Get the relative path after the directory
                relative = file_path[len(prefix) :]
                # Get only the first component (direct child)
                first_part = relative.split("/")[0]
                children.add(first_part)

        return [Path(path_str) / name for name in sorted(children)]

    def load_file(self, path: Path) -> Dict[str, Any]:
        """Load file contents."""
        path_str = str(path)
        if path_str not in self.filesystem:
            raise ConfigError(f"File not found: {path}", "test", path)
        return self.filesystem[path_str]


@dataclass
class SampleConfig:
    """Sample configuration dataclass for testing."""

    name: str
    value: int = 42
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SampleConfig":
        return cls(**data)


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_basic_initialization(self):
        """Test basic manager initialization."""
        mgr = ConfigManager()
        assert mgr.app_name == "3viz"
        assert len(mgr.specs) == 0
        assert len(mgr._cache) == 0

    def test_register_spec(self):
        """Test registering configuration specs."""
        mgr = ConfigManager()
        spec = ConfigSpec(name="test", pattern="test.yaml")

        mgr.register(spec)
        assert "test" in mgr.specs
        assert mgr.specs["test"] == spec

    def test_register_duplicate_fails(self):
        """Test that registering duplicate spec fails."""
        mgr = ConfigManager()
        spec = ConfigSpec(name="test", pattern="test.yaml")

        mgr.register(spec)
        with pytest.raises(ValueError, match="already registered"):
            mgr.register(spec)

    def test_get_unknown_config_fails(self):
        """Test getting unknown config fails."""
        mgr = ConfigManager()

        with pytest.raises(ValueError, match="Unknown config"):
            mgr.get("unknown")

    def test_single_file_loading(self):
        """Test loading a single configuration file."""
        filesystem = {
            "/home/user/.config/3viz/test.yaml": {
                "name": "user-config",
                "value": 100,
            }
        }

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(name="test", pattern="test.yaml")
        mgr.register(spec)

        result = mgr.get("test")
        assert result["name"] == "user-config"
        assert result["value"] == 100

    def test_hierarchical_merge(self):
        """Test configuration merging across hierarchy."""
        filesystem = {
            "/app/config/test.yaml": {
                "name": "default",
                "value": 1,
                "extra": "base",
            },
            "/home/user/.config/3viz/test.yaml": {"name": "user", "value": 2},
            "/project/.3viz/test.yaml": {"value": 3},
        }

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[
                Path("/app/config"),
                Path("/home/user/.config/3viz"),
                Path("/project/.3viz"),
            ],
            file_loader=loader,
        )

        spec = ConfigSpec(name="test", pattern="test.yaml", merge=True)
        mgr.register(spec)

        result = mgr.get("test")
        # Later paths override earlier ones
        assert result["name"] == "user"  # From user config
        assert result["value"] == 3  # From project config
        assert result["extra"] == "base"  # From base config

    def test_collection_loading(self):
        """Test loading a collection of files."""
        filesystem = {
            "/app/config/adapters/adapter1.yaml": {
                "name": "adapter1",
                "type": "builtin",
            },
            "/app/config/adapters/adapter2.yaml": {
                "name": "adapter2",
                "type": "builtin",
            },
            "/home/user/.config/3viz/adapters/custom.yaml": {
                "name": "custom",
                "type": "user",
            },
            "/home/user/.config/3viz/adapters/another.json": {
                "name": "another",
                "type": "user",
            },
        }

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/app/config"), Path("/home/user/.config/3viz")],
            file_loader=loader,
        )

        spec = ConfigSpec(
            name="adapters", pattern="adapters/*.yaml", collection=True
        )
        mgr.register(spec)

        result = mgr.get("adapters")
        assert len(result) == 3  # Only .yaml files match
        names = [r["name"] for r in result]
        assert "adapter1" in names
        assert "adapter2" in names
        assert "custom" in names
        assert "another" not in names  # .json doesn't match pattern

    def test_dataclass_conversion(self):
        """Test automatic dataclass conversion."""
        filesystem = {
            "/home/user/.config/3viz/sample.yaml": {
                "name": "test-config",
                "value": 123,
            }
        }

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(
            name="sample", pattern="sample.yaml", dataclass=SampleConfig
        )
        mgr.register(spec)

        result = mgr.get("sample")
        assert isinstance(result, SampleConfig)
        assert result.name == "test-config"
        assert result.value == 123
        assert result.enabled is True  # Default value

    def test_validation(self):
        """Test configuration validation."""
        filesystem = {
            "/home/user/.config/3viz/validated.yaml": {
                "name": "test",
                "value": -1,
            }
        }

        def validate_positive(data: Dict[str, Any]) -> bool:
            return data.get("value", 0) > 0

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(
            name="validated",
            pattern="validated.yaml",
            validator=validate_positive,
        )
        mgr.register(spec)

        with pytest.raises(ConfigError, match="Validation failed"):
            mgr.get("validated")

    def test_callback(self):
        """Test post-load callback."""
        filesystem = {"/home/user/.config/3viz/callback.yaml": {"name": "test"}}

        processed = []

        def process_config(data):
            processed.append(data["name"])

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(
            name="callback", pattern="callback.yaml", callback=process_config
        )
        mgr.register(spec)

        mgr.get("callback")
        assert processed == ["test"]

    def test_caching(self):
        """Test configuration caching."""
        filesystem = {"/home/user/.config/3viz/cached.yaml": {"count": 1}}

        load_count = 0
        original_load = MockFileLoader.load_file

        def counting_load(self, path):
            nonlocal load_count
            load_count += 1
            return original_load(self, path)

        loader = MockFileLoader(filesystem)
        loader.load_file = counting_load.__get__(loader, MockFileLoader)

        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(name="cached", pattern="cached.yaml")
        mgr.register(spec)

        # First call loads from disk
        result1 = mgr.get("cached")
        assert load_count == 1
        assert result1["count"] == 1

        # Second call uses cache
        result2 = mgr.get("cached")
        assert load_count == 1  # No additional load
        assert result2 is result1  # Same object

        # Force reload
        result3 = mgr.get("cached", force_reload=True)
        assert load_count == 2
        assert result3["count"] == 1

    def test_clear_cache(self):
        """Test cache clearing."""
        filesystem = {
            "/home/user/.config/3viz/test1.yaml": {"name": "test1"},
            "/home/user/.config/3viz/test2.yaml": {"name": "test2"},
        }

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        mgr.register(ConfigSpec(name="test1", pattern="test1.yaml"))
        mgr.register(ConfigSpec(name="test2", pattern="test2.yaml"))

        # Load both configs
        mgr.get("test1")
        mgr.get("test2")
        assert len(mgr._cache) == 2

        # Clear specific cache
        mgr.clear_cache("test1")
        assert len(mgr._cache) == 1
        assert "test2" in mgr._cache

        # Clear all cache
        mgr.clear_cache()
        assert len(mgr._cache) == 0

    def test_error_propagation(self):
        """Test that errors are properly propagated."""
        filesystem = {
            "/home/user/.config/3viz/broken.yaml": {"incomplete": "data"}
        }

        @dataclass
        class StrictConfig:
            required_field: str  # No default

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(
            name="broken", pattern="broken.yaml", dataclass=StrictConfig
        )
        mgr.register(spec)

        with pytest.raises(ConfigError) as exc_info:
            mgr.get("broken")

        assert "Failed to create StrictConfig" in str(exc_info.value)
        assert exc_info.value.spec_name == "broken"

    def test_pattern_matching(self):
        """Test various pattern matching scenarios."""
        spec = ConfigSpec(name="test", pattern="*.yaml")

        assert spec.matches("config.yaml")
        assert spec.matches("my-config.yaml")
        assert not spec.matches("config.yml")
        assert not spec.matches("config.json")

        # Test with directory prefix - now uses full relative path
        spec_with_dir = ConfigSpec(name="test", pattern="themes/*.yaml")
        assert spec_with_dir.matches("themes/default.yaml")
        assert spec_with_dir.matches("themes/custom.yaml")
        assert not spec_with_dir.matches("config.yaml")  # Not in themes/
        assert not spec_with_dir.matches("other/config.yaml")  # Wrong directory

        # Test more complex patterns
        spec_nested = ConfigSpec(name="test", pattern="themes/*/*.yaml")
        assert spec_nested.matches("themes/dark/colors.yaml")
        assert spec_nested.matches("themes/light/colors.yaml")
        assert not spec_nested.matches(
            "themes/colors.yaml"
        )  # Not nested enough

    def test_deep_merge(self):
        """Test deep dictionary merging."""
        mgr = ConfigManager()

        base = {
            "level1": {"level2": {"a": 1, "b": 2}, "value": "base"},
            "top": "original",
        }

        override = {
            "level1": {"level2": {"b": 3, "c": 4}, "value": "override"},
            "new": "added",
        }

        result = mgr._deep_merge(base, override)

        assert result["level1"]["level2"]["a"] == 1  # From base
        assert result["level1"]["level2"]["b"] == 3  # Overridden
        assert result["level1"]["level2"]["c"] == 4  # New
        assert result["level1"]["value"] == "override"
        assert result["top"] == "original"
        assert result["new"] == "added"

    def test_search_path_order(self):
        """Test that search paths have correct precedence order."""
        from unittest.mock import patch

        filesystem = {
            "/app/treeviz/config": {},  # Built-in location
            "/home/user/.config/3viz": {},  # XDG location
            "/project/work/.3viz": {},  # Project location
        }

        loader = MockFileLoader(filesystem)

        # Mock various path operations
        with patch(
            "clier.config.manager.__file__", "/app/clier/config/manager.py"
        ):
            with patch("pathlib.Path.home", return_value=Path("/home/user")):
                with patch(
                    "pathlib.Path.cwd", return_value=Path("/project/work")
                ):
                    with patch.dict(
                        "os.environ", {}, clear=True
                    ):  # No XDG_CONFIG_HOME
                        mgr = ConfigManager(
                            file_loader=loader,
                            package_config_path=Path("/app/treeviz/config"),
                        )
                        paths = mgr.search_paths

                        # Verify order: built-in -> user -> project
                        assert len(paths) == 3
                        assert str(paths[0]) == "/app/treeviz/config"
                        assert str(paths[1]) == "/home/user/.config/3viz"
                        assert str(paths[2]) == "/project/work/.3viz"

    def test_parameterized_loading(self):
        """Test loading with parameters."""
        filesystem = {
            "/home/user/.config/3viz/themes/custom.yaml": {
                "name": "custom",
                "styles": {"color": "red"},
            },
            "/home/user/.config/3viz/themes/dark.yaml": {
                "name": "dark",
                "styles": {"color": "black"},
            },
        }

        loader = MockFileLoader(filesystem)
        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(name="theme", pattern="themes/{name}.yaml")
        mgr.register(spec)

        # Load specific theme
        result = mgr.get("theme", params={"name": "custom"})
        assert result["name"] == "custom"
        assert result["styles"]["color"] == "red"

        # Load different theme
        result = mgr.get("theme", params={"name": "dark"})
        assert result["name"] == "dark"
        assert result["styles"]["color"] == "black"

    def test_parameterized_caching(self):
        """Test that parameterized configs are cached separately."""
        filesystem = {
            "/home/user/.config/3viz/themes/a.yaml": {"name": "a"},
            "/home/user/.config/3viz/themes/b.yaml": {"name": "b"},
        }

        load_count = 0
        original_load = MockFileLoader.load_file

        def counting_load(self, path):
            nonlocal load_count
            load_count += 1
            return original_load(self, path)

        loader = MockFileLoader(filesystem)
        loader.load_file = counting_load.__get__(loader, MockFileLoader)

        mgr = ConfigManager(
            search_paths=[Path("/home/user/.config/3viz")], file_loader=loader
        )

        spec = ConfigSpec(name="theme", pattern="themes/{name}.yaml")
        mgr.register(spec)

        # First load
        mgr.get("theme", params={"name": "a"})
        assert load_count == 1

        # Second load of same - should be cached
        mgr.get("theme", params={"name": "a"})
        assert load_count == 1

        # Load different params - should not be cached
        mgr.get("theme", params={"name": "b"})
        assert load_count == 2

        # Clear cache for specific name clears all variants
        mgr.clear_cache("theme")
        mgr.get("theme", params={"name": "a"})
        assert load_count == 3
