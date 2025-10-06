"""
Tests for the Theme class.
"""

from treeviz.rendering.theme import Theme


class TestTheme:
    """Test Theme functionality."""

    def test_basic_initialization(self):
        """Test basic theme creation."""
        theme = Theme(name="test")
        assert theme.name == "test"
        assert theme.styles == {}

    def test_from_dict(self):
        """Test creating theme from dictionary."""
        config = {
            "name": "custom",
            "styles": {
                "icon": {"light": "#000", "dark": "#FFF"},
                "label": {"light": "black", "dark": "white"},
                "emphasis": "bold",
            },
        }

        theme = Theme.from_dict(config)
        assert theme.name == "custom"
        assert theme.styles["icon"]["light"] == "#000"
        assert theme.styles["icon"]["dark"] == "#FFF"
        assert theme.styles["emphasis"] == "bold"

    def test_from_dict_minimal(self):
        """Test from_dict with minimal config."""
        theme = Theme.from_dict({})
        assert theme.name == "custom"  # Default name
        assert theme.styles == {}

    def test_get_style_simple(self):
        """Test getting simple string styles."""
        theme = Theme(name="test", styles={"emphasis": "bold", "muted": "dim"})

        assert theme.get_style("emphasis") == "bold"
        assert theme.get_style("emphasis", is_dark=True) == "bold"
        assert theme.get_style("muted") == "dim"

    def test_get_style_light_dark(self):
        """Test getting light/dark variant styles."""
        theme = Theme(
            name="test",
            styles={
                "icon": {"light": "#000", "dark": "#FFF"},
                "label": {"light": "black", "dark": "white"},
            },
        )

        # Light mode
        assert theme.get_style("icon", is_dark=False) == "#000"
        assert theme.get_style("label", is_dark=False) == "black"

        # Dark mode
        assert theme.get_style("icon", is_dark=True) == "#FFF"
        assert theme.get_style("label", is_dark=True) == "white"

    def test_get_style_missing(self):
        """Test getting non-existent style."""
        theme = Theme(name="test", styles={})

        assert theme.get_style("missing") is None
        assert theme.get_style("missing", is_dark=True) is None

    def test_merge_themes(self):
        """Test merging two themes."""
        theme1 = Theme(
            name="base",
            styles={
                "icon": {"light": "#000", "dark": "#FFF"},
                "label": {"light": "black", "dark": "white"},
                "emphasis": "bold",
            },
        )

        theme2 = Theme(
            name="override",
            styles={
                "icon": {"light": "red"},  # Partial override
                "label": "blue",  # Full override
                "warning": "orange",  # New style
            },
        )

        merged = theme1.merge(theme2)

        # Name from theme2
        assert merged.name == "override"

        # Icon: merged dict (light from theme2, dark from theme1)
        assert merged.styles["icon"]["light"] == "red"
        assert merged.styles["icon"]["dark"] == "#FFF"

        # Label: completely overridden
        assert merged.styles["label"] == "blue"

        # Emphasis: from theme1
        assert merged.styles["emphasis"] == "bold"

        # Warning: new from theme2
        assert merged.styles["warning"] == "orange"

    def test_merge_with_empty(self):
        """Test merging with empty theme."""
        theme1 = Theme(name="base", styles={"icon": "#000", "label": "black"})

        theme2 = Theme(name="", styles={})

        merged = theme1.merge(theme2)

        # Name from theme1 since theme2 is empty
        assert merged.name == "base"

        # All styles from theme1
        assert merged.styles == theme1.styles

    def test_merge_preserves_originals(self):
        """Test that merge doesn't modify original themes."""
        theme1 = Theme(name="base", styles={"icon": {"light": "#000"}})

        theme2 = Theme(name="override", styles={"icon": {"dark": "#FFF"}})

        merged = theme1.merge(theme2)

        # Originals unchanged
        assert theme1.styles["icon"] == {"light": "#000"}
        assert theme2.styles["icon"] == {"dark": "#FFF"}

        # Merged has both
        assert merged.styles["icon"] == {"light": "#000", "dark": "#FFF"}
