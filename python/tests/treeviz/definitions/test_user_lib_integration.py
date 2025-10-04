"""
Integration tests for user library loading.

Tests the complete integration of user-defined adapters with the adapter library system.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from treeviz.definitions.lib import AdapterLib
from treeviz.adapters.utils import load_adapter


class TestUserLibIntegration:
    """Test user library integration with AdapterLib."""

    def setup_method(self):
        """Set up test environment."""
        # Clear adapter registry for clean tests
        AdapterLib.clear()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

        self.mock_cwd = self.test_root / "cwd"
        self.mock_home = self.test_root / "home"
        self.mock_xdg = self.test_root / "xdg"

        self.mock_cwd.mkdir()
        self.mock_home.mkdir()
        self.mock_xdg.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        AdapterLib.clear()

    def test_load_user_libs_discovers_and_loads_definitions(self):
        """Test that load_user_libs discovers and loads user definitions."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create user config with valid definition
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "custom_adapter.json").write_text(
            '{"label": "custom_label", "type": "custom_type"}'
        )

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            AdapterLib.load_user_libs()

            # Should be able to get the user adapter
            adapter_def = AdapterLib.get("custom_adapter")
            assert adapter_def.label == "custom_label"
            assert adapter_def.type == "custom_type"

    def test_built_in_adapters_have_priority_over_user_adapters(self):
        """Test that built-in adapters are prioritized over user adapters with same name."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create user config that conflicts with built-in name
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "mdast.yaml").write_text(
            "label: user_mdast\ntype: user_type"
        )

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            # Load built-ins first, then user libs
            AdapterLib.load_core_libs()
            AdapterLib.load_user_libs()

            # Should get the built-in mdast, not the user one
            adapter_def = AdapterLib.get("mdast")
            assert adapter_def.label == "value"  # Built-in mdast uses "value"
            assert adapter_def.type == "type"  # Built-in mdast uses "type"

    def test_invalid_user_definitions_are_silently_skipped(self):
        """Test that invalid user definitions don't break loading."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "invalid.json").write_text(
            '{"invalid": json'
        )  # Invalid JSON
        (cwd_config / "valid.json").write_text('{"label": "valid_label"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            # Should not raise exception
            AdapterLib.load_user_libs()

            # Valid adapter should be loaded
            adapter_def = AdapterLib.get("valid")
            assert adapter_def.label == "valid_label"

            # Invalid adapter should not be in registry
            with pytest.raises(KeyError):
                AdapterLib.get("invalid")

    def test_list_formats_includes_user_adapters(self):
        """Test that list_formats includes user-defined adapters."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "user_adapter.json").write_text('{"label": "user_label"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            AdapterLib.load_core_libs()
            AdapterLib.load_user_libs()

            formats = AdapterLib.list_formats()
            assert "user_adapter" in formats
            assert "mdast" in formats  # Built-in
            assert "3viz" in formats

    def test_ensure_all_loaded_loads_both_types(self):
        """Test that ensure_all_loaded loads both built-in and user libraries."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "user_adapter.json").write_text('{"label": "user_label"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            # Clear loading flags
            AdapterLib._loaded = False
            AdapterLib._user_loaded = False

            AdapterLib.ensure_all_loaded()

            assert AdapterLib._loaded is True
            assert AdapterLib._user_loaded is True

            # Should have both built-in and user adapters
            assert "mdast" in AdapterLib._registry
            assert "user_adapter" in AdapterLib._registry


class TestLoadAdapterIntegration:
    """Test load_adapter function with user-defined adapters."""

    def setup_method(self):
        """Set up test environment."""
        AdapterLib.clear()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

        self.mock_cwd = self.test_root / "cwd"
        self.mock_home = self.test_root / "home"
        self.mock_xdg = self.test_root / "xdg"

        self.mock_cwd.mkdir()
        self.mock_home.mkdir()
        self.mock_xdg.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
        AdapterLib.clear()

    def test_load_adapter_finds_user_defined_adapter(self):
        """Test that load_adapter can find and load user-defined adapters."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create user adapter
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "my_format.json").write_text(
            """
        {
            "label": "my_label",
            "type": "my_type",
            "icons": {"node": "⊕"}
        }
        """
        )

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            # Load the user adapter by name
            adapter_dict, icons_dict = load_adapter("my_format")

            assert adapter_dict["label"] == "my_label"
            assert adapter_dict["type"] == "my_type"
            assert icons_dict["node"] == "⊕"

    def test_load_adapter_prefers_built_in_over_user(self):
        """Test that load_adapter prefers built-in adapters over user ones."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create user adapter with same name as built-in
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "mdast.yaml").write_text(
            """
label: user_mdast
type: user_type
        """
        )

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            adapter_dict, icons_dict = load_adapter("mdast")

            # Should get built-in mdast adapter
            assert adapter_dict["label"] == "value"  # Built-in default
            assert adapter_dict["type"] == "type"  # Built-in default

    def test_load_adapter_error_message_includes_user_adapters(self):
        """Test that error message for unknown adapter includes user adapters."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create user adapter
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "user_adapter.json").write_text('{"label": "test"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
            patch("treeviz.definitions.user_config.os.environ", env_vars),
        ):
            with pytest.raises(ValueError) as exc_info:
                load_adapter("nonexistent_adapter")

            error_message = str(exc_info.value)
            assert "user_adapter" in error_message
            assert "mdast" in error_message  # Built-in
            assert "Available adapters:" in error_message
