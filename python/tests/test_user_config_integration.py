"""
Integration tests for user configuration discovery.

This module contains a small set of integration tests that verify user config
discovery works with realistic directory structures.
"""

import tempfile
from pathlib import Path


from treeviz.definitions.user_config import discover_user_definitions


class TestUserConfigIntegration:
    """Integration tests for user configuration discovery."""

    def setup_method(self):
        """Set up realistic directory structure for integration testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)

        # Create mock home, cwd, and xdg directories
        self.user_home = self.test_root / "home" / "user"
        self.user_home.mkdir(parents=True)

        self.project_dir = self.test_root / "projects" / "myproject"
        self.project_dir.mkdir(parents=True)

        self.xdg_config = self.test_root / "config"
        self.xdg_config.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_realistic_user_config_discovery(self):
        """Test discovery with realistic multi-level configuration setup."""
        # Set up environment to use our test directories
        env_vars = {
            "XDG_CONFIG_HOME": str(self.xdg_config),
        }

        # Create user config directories with different types of adapters

        # 1. Project-specific adapters (./.3viz)
        project_config = self.project_dir / ".3viz"
        project_config.mkdir()
        (project_config / "project_specific.json").write_text(
            '{"label": "projectLabel", "type": "projectType"}'
        )

        # 2. User XDG config (XDG_CONFIG_HOME/3viz)
        xdg_3viz = self.xdg_config / "3viz"
        xdg_3viz.mkdir()
        (xdg_3viz / "global_adapter.yaml").write_text(
            "label: globalLabel\ntype: globalType"
        )

        # 3. User home config (~/.3viz)
        home_config = self.user_home / ".3viz"
        home_config.mkdir()
        (home_config / "personal.yml").write_text("label: personalLabel")
        (home_config / "work.json").write_text('{"label": "workLabel"}')

        # Mock the path functions to use our test directories
        import pathlib
        from unittest.mock import patch

        with (
            patch.object(pathlib.Path, "cwd", return_value=self.project_dir),
            patch.object(pathlib.Path, "home", return_value=self.user_home),
        ):
            discovered = discover_user_definitions(env_vars)

            # Verify all three config directories are discovered
            assert len(discovered) == 3

            # Check project directory
            assert project_config in discovered
            project_files = [f.name for f in discovered[project_config]]
            assert "project_specific.json" in project_files

            # Check XDG config directory
            assert xdg_3viz in discovered
            xdg_files = [f.name for f in discovered[xdg_3viz]]
            assert "global_adapter.yaml" in xdg_files

            # Check home config directory
            assert home_config in discovered
            home_files = [f.name for f in discovered[home_config]]
            assert "personal.yml" in home_files
            assert "work.json" in home_files

    def test_no_user_configs_found(self):
        """Test behavior when no user configs are found."""
        env_vars = {
            "XDG_CONFIG_HOME": str(self.xdg_config),
        }

        # Don't create any config directories
        import pathlib
        from unittest.mock import patch

        with (
            patch.object(pathlib.Path, "cwd", return_value=self.project_dir),
            patch.object(pathlib.Path, "home", return_value=self.user_home),
        ):
            discovered = discover_user_definitions(env_vars)

            # Should return empty dict
            assert discovered == {}

    def test_partial_user_configs(self):
        """Test discovery with only some config directories present."""
        env_vars = {
            "XDG_CONFIG_HOME": str(self.xdg_config),
        }

        # Only create home config, not project or XDG
        home_config = self.user_home / ".3viz"
        home_config.mkdir()
        (home_config / "adapter.json").write_text('{"label": "test"}')

        # Create XDG directory but with no definition files
        xdg_3viz = self.xdg_config / "3viz"
        xdg_3viz.mkdir()
        (xdg_3viz / "readme.txt").write_text("No definitions here")

        import pathlib
        from unittest.mock import patch

        with (
            patch.object(pathlib.Path, "cwd", return_value=self.project_dir),
            patch.object(pathlib.Path, "home", return_value=self.user_home),
        ):
            discovered = discover_user_definitions(env_vars)

            # Only home config should be discovered
            assert len(discovered) == 1
            assert home_config in discovered
            assert discovered[home_config][0].name == "adapter.json"
