"""
Tests for the theme system.
"""

import os
from unittest.mock import patch, MagicMock

from treeviz.rendering.themes import (
    DARK_THEME,
    LIGHT_THEME,
    detect_terminal_mode,
    ThemeManager,
    theme_manager,
)
from treeviz.rendering.themes.definitions import Colors


class TestThemeDefinitions:
    """Test theme definitions."""

    def test_dark_theme_has_required_styles(self):
        """Dark theme should have all required style definitions."""
        required_styles = [
            "icon",
            "label",
            "extras",
            "numlines",
            "position",
            "type",
            "default",
            "muted",
            "subdued",
            "faint",
            "info",
            "emphasis",
            "strong",
            "warning",
            "error",
            "success",
        ]
        for style in required_styles:
            assert style in DARK_THEME.styles

    def test_light_theme_has_required_styles(self):
        """Light theme should have all required style definitions."""
        required_styles = [
            "icon",
            "label",
            "extras",
            "numlines",
            "position",
            "type",
            "default",
            "muted",
            "subdued",
            "faint",
            "info",
            "emphasis",
            "strong",
            "warning",
            "error",
            "success",
        ]
        for style in required_styles:
            assert style in LIGHT_THEME.styles

    def test_color_contrast(self):
        """Verify colors have appropriate contrast."""
        # Primary text should be black on light, white on dark
        assert Colors.PRIMARY_LIGHT == "#000000"
        assert Colors.PRIMARY_DARK == "#FFFFFF"

        # Subdued colors should be less prominent
        assert Colors.SUBDUED_LIGHT == "#495057"
        assert Colors.SUBDUED_DARK == "#ADB5BD"


class TestTerminalDetection:
    """Test terminal mode detection."""

    def test_env_override(self):
        """Environment variable should override detection."""
        with patch.dict(os.environ, {"TREEVIZ_THEME": "light"}):
            assert detect_terminal_mode() == "light"

        with patch.dict(os.environ, {"TREEVIZ_THEME": "dark"}):
            assert detect_terminal_mode() == "dark"

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_macos_dark_mode(self, mock_run):
        """macOS dark mode detection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Dark"
        mock_run.return_value = mock_result

        assert detect_terminal_mode() == "dark"

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_macos_light_mode(self, mock_run):
        """macOS light mode detection (no dark mode set)."""
        mock_result = MagicMock()
        mock_result.returncode = 1  # Command fails when not in dark mode
        mock_run.return_value = mock_result

        assert detect_terminal_mode() == "light"

    @patch("sys.platform", "linux")
    def test_linux_colorfgbg_dark(self):
        """Linux COLORFGBG detection for dark background."""
        with patch.dict(os.environ, {"COLORFGBG": "15;0"}):  # White on black
            assert detect_terminal_mode() == "dark"

    @patch("sys.platform", "linux")
    def test_linux_colorfgbg_light(self):
        """Linux COLORFGBG detection for light background."""
        with patch.dict(os.environ, {"COLORFGBG": "0;15"}):  # Black on white
            assert detect_terminal_mode() == "light"

    @patch("sys.platform", "linux")
    def test_default_fallback(self):
        """Should default to dark when detection fails."""
        with patch.dict(os.environ, {}, clear=True):
            assert detect_terminal_mode() == "dark"


class TestThemeManager:
    """Test theme manager functionality."""

    def setup_method(self):
        """Reset ThemeManager before each test."""
        theme_manager.reset()

    def test_module_level_singleton(self):
        """Should use the module-level singleton instance."""
        # The module-level instance should be the one we're using
        assert theme_manager is not None
        assert isinstance(theme_manager, ThemeManager)

    def test_initial_theme_detection(self):
        """Manager should detect theme on initialization."""
        # Reset to ensure clean state
        theme_manager.reset()
        assert theme_manager.active_mode in ("dark", "light")
        assert theme_manager.active_theme is not None

    def test_set_mode(self):
        """Setting mode should update theme."""
        theme_manager.set_mode("dark")
        assert theme_manager.active_mode == "dark"
        assert theme_manager.active_theme == DARK_THEME

        theme_manager.set_mode("light")
        assert theme_manager.active_mode == "light"
        assert theme_manager.active_theme == LIGHT_THEME

    def test_get_console(self):
        """Should return configured console."""
        console = theme_manager.get_console()

        assert console is not None
        # Rich doesn't expose theme as public attribute
        # Just verify console was created

    def test_console_caching(self):
        """Consoles should be cached with same parameters."""
        console1 = theme_manager.get_console(width=80)
        console2 = theme_manager.get_console(width=80)
        assert console1 is console2

        console3 = theme_manager.get_console(width=100)
        assert console3 is not console1

    def test_get_style(self):
        """Should return style values from active theme."""
        theme_manager.set_mode("dark")

        # Should return style from theme
        icon_style = theme_manager.get_style("icon")
        # Rich normalizes hex colors to lowercase
        assert icon_style == Colors.ICON_DARK.lower()

        # Should return empty string for unknown style
        assert theme_manager.get_style("unknown_style") == ""

    def test_custom_theme_registration(self):
        """Should support custom theme registration."""
        from rich.theme import Theme

        custom_theme = Theme({"custom": "red"})

        theme_manager.register_theme("my_theme", custom_theme)
        theme_manager.set_theme("my_theme")

        assert theme_manager.active_theme == custom_theme

    def test_no_color_console(self):
        """No-color console should have no theme."""
        console = theme_manager.get_console(no_color=True)

        # Verify console has no color output
        assert console.no_color is True
