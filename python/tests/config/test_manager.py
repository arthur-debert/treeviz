"""Tests for the configuration manager."""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from config import ConfigManager, ConfigSpec, ConfigError


class MockFileLoader:
    """Mock file loader for testing."""

    def __init__(self, filesystem: Dict[str, Any] = None):
        """
        Initialize with a mock filesystem.

        The filesystem dict maps directory paths to their contents.
        File values are the actual config dictionaries.

        Example:
            {
                "/home/user/.config/3viz": {
                    "test.yaml": {"key": "value"},
                    "subdir": {
                        "nested.yaml": {"other": "data"}
                    }
                }
            }
        """
        self.filesystem = filesystem or {}

    def exists(self, path: Path) -> bool:
        """Check if path exists in mock filesystem."""
        path_str = str(path)

        # Check if it's a known directory
        if path_str in self.filesystem:
            return True

        # Check if it's a file or subdirectory in a known directory
        parent = str(path.parent)
        if parent in self.filesystem:
            parent_contents = self.filesystem[parent]
            if (
                isinstance(parent_contents, dict)
                and path.name in parent_contents
            ):
                return True

        # Check for nested subdirectories (e.g., /app/config/adapters)
        # when filesystem has /app/config with adapters as a key
        parts = path_str.split("/")
        if len(parts) > 2:
            # Try to find the base directory and navigate down
            for i in range(len(parts) - 1, 0, -1):
                base_path = "/".join(parts[:i])
                if base_path in self.filesystem:
                    # Navigate through the remaining parts
                    current = self.filesystem[base_path]
                    for part in parts[i:]:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            return False
                    return True

        return False

    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        # Must have a file extension to be considered a file
        if not path.name.endswith((".yaml", ".yml", ".json")):
            return False

        # Try direct parent lookup
        parent = str(path.parent)
        if parent in self.filesystem:
            parent_contents = self.filesystem[parent]
            if (
                isinstance(parent_contents, dict)
                and path.name in parent_contents
            ):
                # Check it's not a subdirectory
                content = parent_contents[path.name]
                return isinstance(content, dict) and not any(
                    k.endswith((".yaml", ".yml", ".json"))
                    or isinstance(v, dict)
                    for k, v in content.items()
                )

        # Try nested structure
        path_parts = str(path).split("/")
        for i in range(len(path_parts) - 2, 0, -1):
            base_path = "/".join(path_parts[:i])
            if base_path in self.filesystem:
                current = self.filesystem[base_path]

                # Navigate to check if file exists
                for j, part in enumerate(path_parts[i:]):
                    if isinstance(current, dict) and part in current:
                        if j == len(path_parts[i:]) - 1:
                            # This should be the file
                            content = current[part]
                            return isinstance(content, dict) and not any(
                                k.endswith((".yaml", ".yml", ".json"))
                                or isinstance(v, dict)
                                for k, v in content.items()
                            )
                        else:
                            current = current[part]
                    else:
                        return False

        return False

    def list_directory(self, path: Path) -> List[Path]:
        """List contents of a directory."""
        path_str = str(path)

        # Direct directory lookup
        if path_str in self.filesystem:
            dir_contents = self.filesystem[path_str]
            if isinstance(dir_contents, dict):
                return [Path(path_str) / name for name in dir_contents.keys()]

        # Check if it's a subdirectory within a known directory
        parent_str = str(path.parent)
        if parent_str in self.filesystem:
            parent_contents = self.filesystem[parent_str]
            if (
                isinstance(parent_contents, dict)
                and path.name in parent_contents
            ):
                subdir = parent_contents[path.name]
                if isinstance(subdir, dict):
                    return [Path(path_str) / name for name in subdir.keys()]

        return []

    def load_file(self, path: Path) -> Dict[str, Any]:
        """Load file contents."""
        # Try direct parent lookup first
        parent = str(path.parent)
        if parent in self.filesystem:
            parent_contents = self.filesystem[parent]
            if (
                isinstance(parent_contents, dict)
                and path.name in parent_contents
            ):
                contents = parent_contents[path.name]

                # Check if it's a file (dict) not a subdirectory
                if isinstance(contents, dict) and not any(
                    k.endswith((".yaml", ".yml", ".json"))
                    or isinstance(v, dict)
                    for k, v in contents.items()
                ):
                    return contents
                elif isinstance(contents, dict):
                    raise ConfigError(
                        f"Path is a directory: {path}", "test", path
                    )
                else:
                    raise ConfigError(
                        f"Invalid file contents: {path}", "test", path
                    )

        # Try navigating through nested structure
        path_parts = str(path).split("/")
        for i in range(len(path_parts) - 2, 0, -1):
            base_path = "/".join(path_parts[:i])
            if base_path in self.filesystem:
                current = self.filesystem[base_path]

                # Navigate to the file
                for j, part in enumerate(path_parts[i:]):
                    if isinstance(current, dict) and part in current:
                        if j == len(path_parts[i:]) - 1:
                            # This should be the file
                            file_content = current[part]
                            if isinstance(file_content, dict) and not any(
                                k.endswith((".yaml", ".yml", ".json"))
                                or isinstance(v, dict)
                                for k, v in file_content.items()
                            ):
                                return file_content
                            else:
                                raise ConfigError(
                                    f"Invalid file at: {path}", "test", path
                                )
                        else:
                            current = current[part]
                    else:
                        break

        raise ConfigError(f"File not found: {path}", "test", path)


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
            "/home/user/.config/3viz": {
                "test.yaml": {"name": "user-config", "value": 100}
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
            "/app/config": {
                "test.yaml": {"name": "default", "value": 1, "extra": "base"}
            },
            "/home/user/.config/3viz": {
                "test.yaml": {"name": "user", "value": 2}
            },
            "/project/.3viz": {"test.yaml": {"value": 3}},
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
            "/app/config": {
                "adapters": {
                    "adapter1.yaml": {"name": "adapter1", "type": "builtin"},
                    "adapter2.yaml": {"name": "adapter2", "type": "builtin"},
                }
            },
            "/home/user/.config/3viz": {
                "adapters": {
                    "custom.yaml": {"name": "custom", "type": "user"},
                    "another.json": {"name": "another", "type": "user"},
                }
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
            "/home/user/.config/3viz": {
                "sample.yaml": {"name": "test-config", "value": 123}
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
            "/home/user/.config/3viz": {
                "validated.yaml": {"name": "test", "value": -1}
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
        filesystem = {
            "/home/user/.config/3viz": {"callback.yaml": {"name": "test"}}
        }

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
        filesystem = {"/home/user/.config/3viz": {"cached.yaml": {"count": 1}}}

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
            "/home/user/.config/3viz": {
                "test1.yaml": {"name": "test1"},
                "test2.yaml": {"name": "test2"},
            }
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
            "/home/user/.config/3viz": {"broken.yaml": {"incomplete": "data"}}
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

        # Test with directory prefix
        # When pattern has a directory component, it extracts just the filename part
        # for matching, since directory filtering happens at a different level
        spec_with_dir = ConfigSpec(name="test", pattern="themes/*.yaml")
        assert spec_with_dir.matches("default.yaml")
        assert spec_with_dir.matches("custom.yaml")
        # This also matches because we only match the filename part
        assert spec_with_dir.matches("config.yaml")

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
