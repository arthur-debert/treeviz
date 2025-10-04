"""
Tests for user configuration directory discovery.

Tests user config directory discovery, validation, and definition file finding.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


from treeviz.definitions.user_config import (
    get_user_config_dirs,
    is_3viz_conf_dir,
    discover_user_definitions,
)


class TestGetUserConfigDirs:
    """Test get_user_config_dirs function."""

    def test_get_user_config_dirs_with_xdg_config_home(self):
        """Test config dirs when XDG_CONFIG_HOME is set."""
        env_vars = {"XDG_CONFIG_HOME": "/custom/config"}

        with (
            patch("pathlib.Path.cwd") as mock_cwd,
            patch("pathlib.Path.home") as mock_home,
        ):
            mock_cwd.return_value = Path("/current/dir")
            mock_home.return_value = Path("/home/user")

            dirs = get_user_config_dirs(env_vars)

            expected = [
                Path("/current/dir/.3viz"),
                Path("/custom/config/3viz"),
                Path("/home/user/.3viz"),
            ]
            assert dirs == expected

    def test_get_user_config_dirs_without_xdg_config_home(self):
        """Test config dirs when XDG_CONFIG_HOME is not set."""
        env_vars = {}  # No XDG_CONFIG_HOME

        with (
            patch("pathlib.Path.cwd") as mock_cwd,
            patch("pathlib.Path.home") as mock_home,
        ):
            mock_cwd.return_value = Path("/current/dir")
            mock_home.return_value = Path("/home/user")

            dirs = get_user_config_dirs(env_vars)

            expected = [
                Path("/current/dir/.3viz"),
                Path("/home/user/.config/3viz"),
                Path("/home/user/.3viz"),
            ]
            assert dirs == expected

    def test_get_user_config_dirs_uses_os_environ_by_default(self):
        """Test that function uses os.environ when env_vars not provided."""
        original_xdg = os.environ.get("XDG_CONFIG_HOME")

        try:
            # Set a test value
            os.environ["XDG_CONFIG_HOME"] = "/test/config"

            with (
                patch("pathlib.Path.cwd") as mock_cwd,
                patch("pathlib.Path.home") as mock_home,
            ):
                mock_cwd.return_value = Path("/current")
                mock_home.return_value = Path("/home")

                dirs = get_user_config_dirs()

                # Should include the XDG path we set
                assert Path("/test/config/3viz") in dirs

        finally:
            # Restore original value
            if original_xdg is not None:
                os.environ["XDG_CONFIG_HOME"] = original_xdg
            elif "XDG_CONFIG_HOME" in os.environ:
                del os.environ["XDG_CONFIG_HOME"]

    def test_get_user_config_dirs_xdg_config_home_empty_string(self):
        """Test behavior when XDG_CONFIG_HOME is empty string."""
        env_vars = {"XDG_CONFIG_HOME": ""}

        with (
            patch("pathlib.Path.cwd") as mock_cwd,
            patch("pathlib.Path.home") as mock_home,
        ):
            mock_cwd.return_value = Path("/current")
            mock_home.return_value = Path("/home")

            dirs = get_user_config_dirs(env_vars)

            # Empty string should be treated as falsy, fall back to ~/.config
            expected = [
                Path("/current/.3viz"),
                Path("/home/.config/3viz"),
                Path("/home/.3viz"),
            ]
            assert dirs == expected


class TestIs3vizConfDir:
    """Test is_3viz_conf_dir function."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_is_3viz_conf_dir_nonexistent_directory(self):
        """Test that nonexistent directory returns False."""
        nonexistent = self.test_dir / "does_not_exist"
        assert not is_3viz_conf_dir(nonexistent)

    def test_is_3viz_conf_dir_empty_directory(self):
        """Test that empty directory returns False."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        assert not is_3viz_conf_dir(empty_dir)

    def test_is_3viz_conf_dir_with_json_file(self):
        """Test that directory with JSON file returns True."""
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        (config_dir / "adapter.json").write_text('{"label": "test"}')
        assert is_3viz_conf_dir(config_dir)

    def test_is_3viz_conf_dir_with_yaml_file(self):
        """Test that directory with YAML file returns True."""
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        (config_dir / "adapter.yaml").write_text("label: test")
        assert is_3viz_conf_dir(config_dir)

    def test_is_3viz_conf_dir_with_yml_file(self):
        """Test that directory with .yml file returns True."""
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        (config_dir / "adapter.yml").write_text("label: test")
        assert is_3viz_conf_dir(config_dir)

    def test_is_3viz_conf_dir_with_config_files(self):
        """Test that directory with config files is still valid."""
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        (config_dir / "config.json").write_text('{"setting": "value"}')
        (config_dir / "adapter.json").write_text('{"label": "test"}')
        assert is_3viz_conf_dir(config_dir)

    def test_is_3viz_conf_dir_only_config_files(self):
        """Test that directory with only config files returns True."""
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        (config_dir / "config.json").write_text('{"setting": "value"}')
        assert is_3viz_conf_dir(config_dir)

    def test_is_3viz_conf_dir_with_non_definition_files(self):
        """Test that directory with only non-definition files returns False."""
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        (config_dir / "readme.txt").write_text("This is a readme")
        (config_dir / "script.py").write_text("print('hello')")
        assert not is_3viz_conf_dir(config_dir)

    def test_is_3viz_conf_dir_file_instead_of_directory(self):
        """Test that passing a file instead of directory returns False."""
        test_file = self.test_dir / "test.json"
        test_file.write_text('{"label": "test"}')
        assert not is_3viz_conf_dir(test_file)


class TestDiscoverUserDefinitions:
    """Test discover_user_definitions function."""

    def setup_method(self):
        """Set up temporary directory structure for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

        # Create mock directories
        self.mock_cwd = self.test_root / "cwd"
        self.mock_xdg = self.test_root / "xdg_config"
        self.mock_home = self.test_root / "home"

        self.mock_cwd.mkdir()
        self.mock_xdg.mkdir()
        self.mock_home.mkdir()

    def teardown_method(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_discover_user_definitions_empty_dirs(self):
        """Test discovery with no valid config directories."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        with (
            patch("pathlib.Path.cwd") as mock_cwd_fn,
            patch("pathlib.Path.home") as mock_home_fn,
        ):
            mock_cwd_fn.return_value = self.mock_cwd
            mock_home_fn.return_value = self.mock_home

            discovered = discover_user_definitions(env_vars)
            assert discovered == {}

    def test_discover_user_definitions_single_directory(self):
        """Test discovery with one valid config directory."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create config directory with definitions
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "my_adapter.json").write_text('{"label": "test"}')
        (cwd_config / "other.yaml").write_text("label: other")

        with (
            patch("pathlib.Path.cwd") as mock_cwd_fn,
            patch("pathlib.Path.home") as mock_home_fn,
        ):
            mock_cwd_fn.return_value = self.mock_cwd
            mock_home_fn.return_value = self.mock_home

            discovered = discover_user_definitions(env_vars)

            assert len(discovered) == 1
            assert cwd_config in discovered
            assert len(discovered[cwd_config]) == 2

            # Check that both files are found
            filenames = [f.name for f in discovered[cwd_config]]
            assert "my_adapter.json" in filenames
            assert "other.yaml" in filenames

    def test_discover_user_definitions_multiple_directories(self):
        """Test discovery with multiple valid config directories."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create multiple config directories
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "cwd_adapter.json").write_text('{"label": "cwd"}')

        xdg_config = self.mock_xdg / "3viz"
        xdg_config.mkdir()
        (xdg_config / "xdg_adapter.yaml").write_text("label: xdg")

        home_config = self.mock_home / ".3viz"
        home_config.mkdir()
        (home_config / "home_adapter.yml").write_text("label: home")

        with (
            patch("pathlib.Path.cwd") as mock_cwd_fn,
            patch("pathlib.Path.home") as mock_home_fn,
        ):
            mock_cwd_fn.return_value = self.mock_cwd
            mock_home_fn.return_value = self.mock_home

            discovered = discover_user_definitions(env_vars)

            assert len(discovered) == 3
            assert cwd_config in discovered
            assert xdg_config in discovered
            assert home_config in discovered

            # Check each has its expected file
            assert discovered[cwd_config][0].name == "cwd_adapter.json"
            assert discovered[xdg_config][0].name == "xdg_adapter.yaml"
            assert discovered[home_config][0].name == "home_adapter.yml"

    def test_discover_user_definitions_skips_config_files(self):
        """Test that config.json and 3viz.yaml files are skipped."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "config.json").write_text('{"setting": "value"}')
        (cwd_config / "3viz.yaml").write_text("setting: value")
        (cwd_config / "adapter.json").write_text('{"label": "test"}')

        with (
            patch("pathlib.Path.cwd") as mock_cwd_fn,
            patch("pathlib.Path.home") as mock_home_fn,
        ):
            mock_cwd_fn.return_value = self.mock_cwd
            mock_home_fn.return_value = self.mock_home

            discovered = discover_user_definitions(env_vars)

            assert len(discovered) == 1
            assert cwd_config in discovered
            assert len(discovered[cwd_config]) == 1
            assert discovered[cwd_config][0].name == "adapter.json"

    def test_discover_user_definitions_mixed_valid_invalid_dirs(self):
        """Test discovery with mix of valid and invalid directories."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Valid directory
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "adapter.json").write_text('{"label": "test"}')

        # Invalid directory (exists but no definition files)
        xdg_config = self.mock_xdg / "3viz"
        xdg_config.mkdir()
        (xdg_config / "readme.txt").write_text("No definitions here")

        # No home config directory

        with (
            patch("pathlib.Path.cwd") as mock_cwd_fn,
            patch("pathlib.Path.home") as mock_home_fn,
        ):
            mock_cwd_fn.return_value = self.mock_cwd
            mock_home_fn.return_value = self.mock_home

            discovered = discover_user_definitions(env_vars)

            # Only the valid directory should be included
            assert len(discovered) == 1
            assert cwd_config in discovered
            assert xdg_config not in discovered

    def test_discover_user_definitions_with_os_environ(self):
        """Test that function uses os.environ by default."""
        original_xdg = os.environ.get("XDG_CONFIG_HOME")

        try:
            # Set test environment
            os.environ["XDG_CONFIG_HOME"] = str(self.mock_xdg)

            # Create config directory
            cwd_config = self.mock_cwd / ".3viz"
            cwd_config.mkdir()
            (cwd_config / "adapter.json").write_text('{"label": "test"}')

            with (
                patch("pathlib.Path.cwd") as mock_cwd_fn,
                patch("pathlib.Path.home") as mock_home_fn,
            ):
                mock_cwd_fn.return_value = self.mock_cwd
                mock_home_fn.return_value = self.mock_home

                # Call without env_vars parameter
                discovered = discover_user_definitions()

                assert len(discovered) == 1
                assert cwd_config in discovered

        finally:
            # Restore original environment
            if original_xdg is not None:
                os.environ["XDG_CONFIG_HOME"] = original_xdg
            elif "XDG_CONFIG_HOME" in os.environ:
                del os.environ["XDG_CONFIG_HOME"]
