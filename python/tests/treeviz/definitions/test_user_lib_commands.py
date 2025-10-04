"""
Tests for user library management commands.

Tests the pure Python functions that implement CLI commands for user library management.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch


from treeviz.definitions.user_lib_commands import (
    list_user_definitions,
    validate_user_definitions,
)


class TestListUserDefinitions:
    """Test list_user_definitions function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

        # Create mock directories
        self.mock_cwd = self.test_root / "cwd"
        self.mock_xdg = self.test_root / "xdg"
        self.mock_home = self.test_root / "home"

        self.mock_cwd.mkdir()
        self.mock_xdg.mkdir()
        self.mock_home.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_list_user_definitions_no_configs(self):
        """Test listing when no configs exist."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = list_user_definitions(env_vars)

            # Should have 3 directories, all not found
            assert len(result["directories"]) == 3
            assert all(
                d["status"] == "not_found" for d in result["directories"]
            )
            assert all(d["file_count"] == 0 for d in result["directories"])

            # Should have no definitions
            assert len(result["definitions"]) == 0

    def test_list_user_definitions_with_configs(self):
        """Test listing with valid config directories."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create config directories with definitions
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "adapter1.json").write_text('{"label": "test"}')

        xdg_config = self.mock_xdg / "3viz"
        xdg_config.mkdir()
        (xdg_config / "adapter2.yaml").write_text("label: test")

        # Home config exists but no definitions (has config files but no adapters)
        home_config = self.mock_home / ".3viz"
        home_config.mkdir()
        (home_config / "config.json").write_text('{"setting": "value"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = list_user_definitions(env_vars)

            # Check directory statuses
            directories = {d["path"]: d for d in result["directories"]}

            assert directories[str(cwd_config)]["status"] == "found"
            assert directories[str(cwd_config)]["file_count"] == 1

            assert directories[str(xdg_config)]["status"] == "found"
            assert directories[str(xdg_config)]["file_count"] == 1

            assert (
                directories[str(home_config)]["status"]
                == "found_no_definitions"
            )
            assert directories[str(home_config)]["file_count"] == 0

            # Check definitions
            assert len(result["definitions"]) == 2

            def_names = [d["name"] for d in result["definitions"]]
            assert "adapter1" in def_names
            assert "adapter2" in def_names

    def test_list_user_definitions_skips_config_files(self):
        """Test that config files are skipped in listing."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "config.json").write_text('{"setting": "value"}')
        (cwd_config / "3viz.yaml").write_text("setting: value")
        (cwd_config / "adapter.json").write_text('{"label": "test"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = list_user_definitions(env_vars)

            # Should only find the adapter, not config files
            assert len(result["definitions"]) == 1
            assert result["definitions"][0]["name"] == "adapter"

            # Directory should show 1 file
            directories = {d["path"]: d for d in result["directories"]}
            assert directories[str(cwd_config)]["file_count"] == 1


class TestValidateUserDefinitions:
    """Test validate_user_definitions function."""

    def setup_method(self):
        """Set up test environment."""
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

    def test_validate_user_definitions_no_definitions(self):
        """Test validation when no definitions exist."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = validate_user_definitions(env_vars)

            assert len(result["valid_definitions"]) == 0
            assert len(result["invalid_definitions"]) == 0
            assert result["summary"]["total_files"] == 0
            assert result["summary"]["success_rate"] == 1.0

    def test_validate_user_definitions_valid_files(self):
        """Test validation with valid definition files."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create valid definitions
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "valid1.json").write_text(
            '{"label": "test_label", "type": "test_type"}'
        )

        xdg_config = self.mock_xdg / "3viz"
        xdg_config.mkdir()
        (xdg_config / "valid2.yaml").write_text(
            "label: another_label\ntype: another_type"
        )

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = validate_user_definitions(env_vars)

            assert len(result["valid_definitions"]) == 2
            assert len(result["invalid_definitions"]) == 0
            assert result["summary"]["total_files"] == 2
            assert result["summary"]["valid_count"] == 2
            assert result["summary"]["invalid_count"] == 0
            assert result["summary"]["success_rate"] == 1.0

            # Check valid definition details
            valid_names = [d["name"] for d in result["valid_definitions"]]
            assert "valid1" in valid_names
            assert "valid2" in valid_names

    def test_validate_user_definitions_invalid_files(self):
        """Test validation with invalid definition files."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        # Create invalid definitions
        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "invalid_json.json").write_text(
            '{"label": "test"'
        )  # Invalid JSON
        (cwd_config / "invalid_structure.yaml").write_text(
            "label: test\ninvalid_field: {invalid: yaml: structure"
        )

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = validate_user_definitions(env_vars)

            assert len(result["valid_definitions"]) == 0
            assert len(result["invalid_definitions"]) == 2
            assert result["summary"]["total_files"] == 2
            assert result["summary"]["valid_count"] == 0
            assert result["summary"]["invalid_count"] == 2
            assert result["summary"]["success_rate"] == 0.0

            # Check invalid definition details
            invalid_names = [d["name"] for d in result["invalid_definitions"]]
            assert "invalid_json" in invalid_names
            assert "invalid_structure" in invalid_names

            # Check that errors are captured
            for invalid_def in result["invalid_definitions"]:
                assert "error" in invalid_def
                assert "error_type" in invalid_def
                assert len(invalid_def["error"]) > 0

    def test_validate_user_definitions_mixed_files(self):
        """Test validation with mix of valid and invalid files."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "valid.json").write_text('{"label": "test"}')
        (cwd_config / "invalid.json").write_text(
            '{"label": "test"'
        )  # Missing closing brace

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = validate_user_definitions(env_vars)

            assert len(result["valid_definitions"]) == 1
            assert len(result["invalid_definitions"]) == 1
            assert result["summary"]["total_files"] == 2
            assert result["summary"]["valid_count"] == 1
            assert result["summary"]["invalid_count"] == 1
            assert result["summary"]["success_rate"] == 0.5

            assert result["valid_definitions"][0]["name"] == "valid"
            assert result["invalid_definitions"][0]["name"] == "invalid"

    def test_validate_user_definitions_skips_config_files(self):
        """Test that config files are not validated."""
        env_vars = {"XDG_CONFIG_HOME": str(self.mock_xdg)}

        cwd_config = self.mock_cwd / ".3viz"
        cwd_config.mkdir()
        (cwd_config / "config.json").write_text('{"setting": "value"}')
        (cwd_config / "3viz.yaml").write_text("setting: value")
        (cwd_config / "adapter.json").write_text('{"label": "test"}')

        with (
            patch("pathlib.Path.cwd", return_value=self.mock_cwd),
            patch("pathlib.Path.home", return_value=self.mock_home),
        ):
            result = validate_user_definitions(env_vars)

            # Should only validate the adapter file, not config files
            assert len(result["valid_definitions"]) == 1
            assert len(result["invalid_definitions"]) == 0
            assert result["summary"]["total_files"] == 1
            assert result["valid_definitions"][0]["name"] == "adapter"
