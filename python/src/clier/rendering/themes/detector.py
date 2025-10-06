"""
Terminal theme detection for treeviz.

Provides OS-specific detection of terminal dark/light mode.
"""

import os
import sys
import subprocess
from typing import Literal


def detect_terminal_mode() -> Literal["dark", "light"]:
    """
    Attempts to detect if the terminal is in dark or light mode.

    Uses platform-specific methods for higher accuracy:
    - macOS: Checks system appearance setting
    - Windows: Checks registry for system/app theme
    - Linux/Other: Checks COLORFGBG environment variable

    Returns:
        'dark' or 'light'. Defaults to 'dark' if detection fails.
    """
    # Allow manual override via environment variable
    if "TREEVIZ_THEME" in os.environ:
        theme = os.environ["TREEVIZ_THEME"].lower()
        if theme in ("dark", "light"):
            return theme

    # macOS: Check system appearance setting
    if sys.platform == "darwin":
        try:
            cmd = "defaults read -g AppleInterfaceStyle"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0 and result.stdout.strip() == "Dark":
                return "dark"
            else:
                return "light"  # Light is default if key doesn't exist
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            pass  # Fall through to default

    # Windows: Check registry for system/app theme
    elif sys.platform == "win32":
        try:
            import winreg

            key_path = (
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                # AppsUseLightTheme: 0 for dark, 1 for light
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value == 1 else "dark"
        except Exception:
            pass  # Fall through to default

    # Linux/Other: Check COLORFGBG environment variable
    elif "COLORFGBG" in os.environ:
        try:
            # COLORFGBG format is "foreground;background"
            # e.g., "15;0" means white on black (dark theme)
            parts = os.environ["COLORFGBG"].split(";")
            if len(parts) >= 2:
                bg = int(parts[1])
                # ANSI colors 0-7 are considered dark backgrounds
                # 0=black, 1=red, 2=green, 3=yellow, 4=blue, 5=magenta, 6=cyan, 7=white
                if 0 <= bg <= 6:
                    return "dark"
                else:
                    return "light"
        except (ValueError, IndexError):
            pass

    # Check common terminal environment variables
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    os.environ.get("COLORTERM", "").lower()

    # Some terminals set specific environment variables
    if term_program in ("iterm.app", "hyper", "alacritty"):
        # These terminals typically use dark themes by default
        return "dark"

    # Default to dark mode - most developer terminals use dark themes
    return "dark"
