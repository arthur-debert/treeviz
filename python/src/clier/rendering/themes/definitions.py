"""
Theme definitions for treeviz.

Defines color schemes for dark and light terminal backgrounds using
semantic names that map to specific colors in each theme.
"""

from rich.theme import Theme


# Color definitions inspired by lipgloss adaptive colors
class Colors:
    """Adaptive color definitions for dark/light themes."""

    # Primary text - main content
    PRIMARY_LIGHT = "#000000"
    PRIMARY_DARK = "#FFFFFF"

    # Subdued text - secondary information
    SUBDUED_LIGHT = "#495057"
    SUBDUED_DARK = "#ADB5BD"

    # Muted text - less important information
    MUTED_LIGHT = "#ADB5BD"
    MUTED_DARK = "#6C757D"

    # Faint text - barely visible
    FAINT_LIGHT = "#CED4DA"
    FAINT_DARK = "#CED4DA"

    # Additional semantic colors
    INFO_LIGHT = "#0066CC"
    INFO_DARK = "#66B3FF"

    WARNING_LIGHT = "#CC6600"
    WARNING_DARK = "#FFB366"

    ERROR_LIGHT = "#CC0000"
    ERROR_DARK = "#FF6666"

    SUCCESS_LIGHT = "#009900"
    SUCCESS_DARK = "#66FF66"

    # Icon colors
    ICON_LIGHT = "#0066CC"
    ICON_DARK = "#66B3FF"

    # Type colors
    TYPE_LIGHT = "#6600CC"
    TYPE_DARK = "#B366FF"


# Dark theme definition
DARK_THEME = Theme(
    {
        # Tree structure elements
        "icon": Colors.ICON_DARK,
        "label": Colors.PRIMARY_DARK,
        "extras": Colors.SUBDUED_DARK,
        "numlines": Colors.MUTED_DARK,
        "position": Colors.FAINT_DARK,
        "type": Colors.TYPE_DARK,
        # Semantic styles
        "default": Colors.PRIMARY_DARK,
        "muted": Colors.MUTED_DARK,
        "subdued": Colors.SUBDUED_DARK,
        "faint": Colors.FAINT_DARK,
        "info": Colors.INFO_DARK,
        "emphasis": f"bold {Colors.PRIMARY_DARK}",
        "strong": f"bold {Colors.PRIMARY_DARK}",
        "warning": Colors.WARNING_DARK,
        "error": Colors.ERROR_DARK,
        "success": Colors.SUCCESS_DARK,
    }
)


# Light theme definition
LIGHT_THEME = Theme(
    {
        # Tree structure elements
        "icon": Colors.ICON_LIGHT,
        "label": Colors.PRIMARY_LIGHT,
        "extras": Colors.SUBDUED_LIGHT,
        "numlines": Colors.MUTED_LIGHT,
        "position": Colors.FAINT_LIGHT,
        "type": Colors.TYPE_LIGHT,
        # Semantic styles
        "default": Colors.PRIMARY_LIGHT,
        "muted": Colors.MUTED_LIGHT,
        "subdued": Colors.SUBDUED_LIGHT,
        "faint": Colors.FAINT_LIGHT,
        "info": Colors.INFO_LIGHT,
        "emphasis": f"bold {Colors.PRIMARY_LIGHT}",
        "strong": f"bold {Colors.PRIMARY_LIGHT}",
        "warning": Colors.WARNING_LIGHT,
        "error": Colors.ERROR_LIGHT,
        "success": Colors.SUCCESS_LIGHT,
    }
)
