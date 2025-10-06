"""
Tests for the theme system.
"""

import os
from unittest.mock import patch, MagicMock

from clier.rendering.themes import (
    detect_terminal_mode,
    theme,
    set_theme_mode,
    get_theme_mode,
    set_theme,
    list_available_themes,
    get_console,
)


class TestThemeSystem:
    """Test the new theme system."""

    def test_theme_proxy_has_required_styles(self):
        """Theme proxy should expose all required style attributes."""
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
            assert hasattr(theme, style)
            # Verify it returns a style proxy
            style_proxy = getattr(theme, style)
            assert hasattr(style_proxy, "style")

    def test_theme_mode_switching(self):
        """Test switching between light and dark modes."""
        # Test dark mode
        set_theme_mode("dark")
        assert get_theme_mode() == "dark"

        # Test light mode
        set_theme_mode("light")
        assert get_theme_mode() == "light"

    def test_list_available_themes(self):
        """Test listing available themes."""
        themes = list_available_themes()
        assert isinstance(themes, list)
        assert "default" in themes
        # Should include themes from clier.config
        assert len(themes) >= 1

    def test_get_console(self):
        """Should return configured console."""
        console = get_console()
        assert console is not None
        # Console objects don't expose theme attribute directly
        # Just verify we got a valid console
        from rich.console import Console

        assert isinstance(console, Console)

    def test_console_force_terminal(self):
        """Should support force terminal option."""
        console1 = get_console(force_terminal=True)
        console2 = get_console(force_terminal=False)
        # They should be different console instances
        assert console1 is not console2

    def test_set_theme(self):
        """Should support changing themes."""
        # Set to a known theme
        set_theme("default")
        # Verify theme is loaded
        assert hasattr(theme, "icon")

        # Try setting a custom theme if available
        themes = list_available_themes()
        if "minimal" in themes:
            set_theme("minimal")
            # Theme should still work
            assert hasattr(theme, "icon")


class TestTerminalDetection:
    """Test terminal theme detection."""

    @patch("sys.platform", "linux")
    def test_detect_terminal_mode_dark(self):
        """Should detect dark mode from environment."""
        # Background 0-6 are dark colors
        # Clear existing env vars that might interfere
        env = {"COLORFGBG": "15;0"}
        with patch.dict(os.environ, env, clear=True):
            assert detect_terminal_mode() == "dark"

    @patch("sys.platform", "linux")
    def test_detect_terminal_mode_light(self):
        """Should detect light mode from environment."""
        # Background 7+ are light colors
        env = {"COLORFGBG": "0;15"}
        with patch.dict(os.environ, env, clear=True):
            assert detect_terminal_mode() == "light"

    @patch("sys.platform", "linux")
    def test_detect_terminal_mode_no_env(self):
        """Should default to dark when no environment info."""
        with patch.dict(os.environ, {}, clear=True):
            assert detect_terminal_mode() == "dark"

    @patch("sys.platform", "linux")
    def test_detect_terminal_mode_invalid_env(self):
        """Should default to dark on invalid environment."""
        with patch.dict(os.environ, {"COLORFGBG": "invalid"}):
            assert detect_terminal_mode() == "dark"

    @patch("sys.platform", "win32")
    def test_detect_terminal_mode_windows(self):
        """Should detect Windows dark mode."""
        # Create a fake winreg module
        mock_winreg = MagicMock()
        mock_key = MagicMock()

        with patch.dict("sys.modules", {"winreg": mock_winreg}):
            mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
            mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"

            # Test dark mode
            mock_winreg.QueryValueEx.return_value = (0, None)
            assert detect_terminal_mode() == "dark"

            # Test light mode
            mock_winreg.QueryValueEx.return_value = (1, None)
            assert detect_terminal_mode() == "light"

    @patch("sys.platform", "darwin")
    def test_detect_terminal_mode_macos(self):
        """Should detect macOS dark mode."""
        # Test dark mode
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Dark"
            mock_run.return_value = mock_result
            assert detect_terminal_mode() == "dark"

        # Test light mode
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1  # Non-zero means no dark mode
            mock_run.return_value = mock_result
            assert detect_terminal_mode() == "light"
