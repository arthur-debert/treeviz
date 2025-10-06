"""
Tests for configuration loaders.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from clier.config import ConfigManager, FileLoader
from treeviz.config.loaders import ConfigLoaders, create_config_loaders
from treeviz.rendering.theme import Theme
from treeviz.rendering.presentation import ViewOptions, ShowTypes, CompactMode
from treeviz.definitions.model import AdapterDef


class MockFileSystem:
    """Mock filesystem for testing config loading."""

    def __init__(self):
        self.files = {
            # Built-in themes
            "/app/treeviz/config/themes/default.yaml": {
                "name": "default",
                "styles": {
                    "icon": {"light": "#000", "dark": "#FFF"},
                    "label": {"light": "#111", "dark": "#EEE"},
                },
            },
            "/app/treeviz/config/themes/minimal.yaml": {
                "name": "minimal",
                "styles": {
                    "icon": {"light": "#333", "dark": "#CCC"},
                    "label": {"light": "#000", "dark": "#FFF"},
                },
            },
            # User themes
            "/home/user/.config/3viz/themes/custom.yaml": {
                "name": "custom",
                "styles": {
                    "icon": {"light": "red", "dark": "cyan"},
                    "label": {"light": "black", "dark": "white"},
                },
            },
            # Built-in adapters
            "/app/treeviz/config/adapters/mdast.yaml": {
                "label": "value",
                "type": "type",
                "children": "children",
                "icons": {"root": "⧉", "paragraph": "¶", "text": "◦"},
            },
            "/app/treeviz/config/adapters/pandoc.yaml": {
                "label": "c",
                "type": "t",
                "children": "c",
                "icons": {"Document": "📄", "Para": "¶"},
            },
            # View configurations at different levels
            "/app/treeviz/config/view.yaml": {
                "max_width": 120,
                "show_line_count": True,
                "show_types": "always",
                "indent_size": 2,
            },
            "/home/user/.config/3viz/view.yaml": {
                "max_width": 100,
                "show_types": "missing",
            },
            "/project/.3viz/view.yaml": {
                "max_width": 80,
                "compact_mode": "hide",
            },
        }

    def create_loader(self) -> FileLoader:
        """Create a mock file loader."""
        loader = Mock()

        def exists(path):
            path_str = str(path)
            # Check if it's a file or a parent directory of any file
            if path_str in self.files:
                return True
            # Check if it's a directory containing files
            for file_path in self.files:
                if file_path.startswith(path_str + "/"):
                    return True
            return False

        def is_file(path):
            return str(path) in self.files

        def list_directory(path):
            path_str = str(path).rstrip("/")
            children = set()

            for file_path in self.files:
                if file_path.startswith(path_str + "/"):
                    relative = file_path[len(path_str) + 1 :]
                    first_part = relative.split("/")[0]
                    children.add(first_part)

            return [Path(path_str) / name for name in sorted(children)]

        def load_file(path):
            path_str = str(path)
            if path_str in self.files:
                return self.files[path_str].copy()
            raise FileNotFoundError(f"File not found: {path}")

        loader.exists = exists
        loader.is_file = is_file
        loader.list_directory = list_directory
        loader.load_file = load_file

        return loader


class TestConfigLoaders:
    """Test configuration loader functionality."""

    @pytest.fixture
    def mock_fs(self):
        """Provide mock filesystem."""
        return MockFileSystem()

    @pytest.fixture
    def loaders(self, mock_fs):
        """Create config loaders with mock filesystem."""
        manager = ConfigManager(
            app_name="3viz",
            search_paths=[
                Path("/app/treeviz/config"),
                Path("/home/user/.config/3viz"),
                Path("/project/.3viz"),
            ],
            file_loader=mock_fs.create_loader(),
        )
        return ConfigLoaders(manager)

    def test_load_all_themes(self, loaders):
        """Test loading all available themes."""
        themes = loaders.load_all_themes()

        # Should find 3 themes total
        assert len(themes) == 3

        # Check theme names
        theme_names = [t.name for t in themes]
        assert "default" in theme_names
        assert "minimal" in theme_names
        assert "custom" in theme_names

        # Verify theme structure
        for theme in themes:
            assert isinstance(theme, Theme)
            assert theme.name
            assert theme.styles

    def test_load_specific_theme(self, loaders):
        """Test loading a specific theme by name."""
        # Load default theme
        theme = loaders.load_theme("default")
        assert theme is not None
        assert theme.name == "default"
        assert theme.styles["icon"]["light"] == "#000"
        assert theme.styles["icon"]["dark"] == "#FFF"

        # Load custom theme
        custom = loaders.load_theme("custom")
        assert custom is not None
        assert custom.name == "custom"
        assert custom.styles["icon"]["light"] == "red"

        # Non-existent theme
        missing = loaders.load_theme("nonexistent")
        assert missing is None

    def test_load_all_adapters(self, loaders):
        """Test loading all adapter definitions."""
        adapters = loaders.load_all_adapters()

        assert len(adapters) == 2

        # Check adapter structure
        for adapter in adapters:
            assert isinstance(adapter, AdapterDef)
            assert adapter.label
            assert adapter.type
            assert adapter.icons

    def test_load_specific_adapter(self, loaders):
        """Test loading a specific adapter by name."""
        # Load mdast adapter
        mdast = loaders.load_adapter("mdast")
        assert mdast is not None
        assert mdast.label == "value"
        assert mdast.type == "type"
        assert mdast.icons["paragraph"] == "¶"

        # Load pandoc adapter
        pandoc = loaders.load_adapter("pandoc")
        assert pandoc is not None
        assert pandoc.label == "c"
        assert pandoc.icons["Document"] == "📄"

        # Non-existent adapter
        missing = loaders.load_adapter("nonexistent")
        assert missing is None

    def test_load_view_options_hierarchy(self, loaders):
        """Test loading view options with hierarchy merging."""
        view = loaders.load_view_options()

        assert isinstance(view, ViewOptions)

        # Project level should override others
        assert view.max_width == 80  # From project
        assert view.show_types == ShowTypes.MISSING  # From user
        assert view.show_line_count is True  # From built-in
        assert view.indent_size == 2  # From built-in
        assert view.compact_mode == CompactMode.HIDE  # From project

    def test_get_theme_names(self, loaders):
        """Test getting list of theme names."""
        names = loaders.get_theme_names()

        assert len(names) == 3
        assert "default" in names
        assert "minimal" in names
        assert "custom" in names

    def test_get_adapter_names(self, loaders):
        """Test getting list of adapter names."""
        names = loaders.get_adapter_names()

        # Now AdapterDef has a name field populated from filename
        assert len(names) == 2
        assert "mdast" in names
        assert "pandoc" in names

    def test_create_config_loaders(self, mock_fs, monkeypatch):
        """Test the factory function."""
        # Mock the default file loader
        monkeypatch.setattr(
            "clier.config.manager.DefaultFileLoader",
            lambda: mock_fs.create_loader(),
        )

        loaders = create_config_loaders(
            search_paths=[Path("/app/treeviz/config")]
        )

        assert isinstance(loaders, ConfigLoaders)
        assert isinstance(loaders.manager, ConfigManager)

        # Verify specs are registered
        assert "themes" in loaders.manager.specs
        assert "theme" in loaders.manager.specs
        assert "adapters" in loaders.manager.specs
        assert "adapter" in loaders.manager.specs
        assert "view" in loaders.manager.specs
