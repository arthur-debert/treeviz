"""
Tests for the template-based renderer.
"""

from treeviz.model import Node
from treeviz.rendering.engines.template import TemplateRenderer
from clier.rendering.themes import set_theme_mode, set_theme
from treeviz.rendering import Presentation


class TestTemplateRenderer:
    """Test the template renderer."""

    def setup_method(self):
        """Reset theme to defaults before each test."""
        set_theme_mode("dark")
        set_theme("default")

    def test_basic_rendering(self):
        """Test basic tree rendering."""
        # Create a simple tree
        root = Node(
            label="Root",
            type="document",
            children=[
                Node(label="Child 1", type="paragraph"),
                Node(label="Child 2", type="paragraph"),
            ],
        )

        renderer = TemplateRenderer()
        presentation = Presentation()
        result = renderer.render(root, presentation)

        # Check basic structure
        assert "Root" in result
        assert "Child 1" in result
        assert "Child 2" in result
        assert "2L" in result  # Root has 2 children
        assert "1L" in result  # Children have no children

    def test_indentation(self):
        """Test proper indentation."""
        root = Node(
            label="Root",
            children=[Node(label="Level 1", children=[Node(label="Level 2")])],
        )

        renderer = TemplateRenderer()
        presentation = Presentation()
        result = renderer.render(root, presentation)
        lines = result.split("\n")

        # Check indentation
        assert lines[0].startswith("?")  # No indent for root
        assert lines[1].startswith("  ?")  # 2 spaces for level 1
        assert lines[2].startswith("    ?")  # 4 spaces for level 2

    def test_extras_formatting(self):
        """Test that extras are formatted correctly."""
        root = Node(
            label="List",
            type="list",
            extra={"type": "ordered", "start": 1},
            children=[Node(label="Item 1"), Node(label="Item 2")],
        )

        renderer = TemplateRenderer()
        presentation = Presentation()
        presentation.view.max_width = 80
        result = renderer.render(root, presentation)

        # Extras should be formatted and displayed
        assert "type=ordered" in result
        assert "start=1" in result

    def test_long_label_truncation(self):
        """Test that long labels are truncated."""
        long_text = (
            "This is a very long label that should be truncated with ellipsis"
        )
        root = Node(label=long_text, type="paragraph")

        renderer = TemplateRenderer()
        presentation = Presentation()
        presentation.view.max_width = 40
        result = renderer.render(root, presentation)

        # Should be truncated
        assert "…" in result
        assert len(result.split("\n")[0]) <= 40

    def test_custom_symbols(self):
        """Test custom symbol overrides."""
        root = Node(label="Custom", type="custom_type")

        renderer = TemplateRenderer()
        presentation = Presentation()
        # Set custom symbols through icons in presentation
        presentation.icons = {"custom_type": "★"}
        result = renderer.render(root, presentation)

        assert "★" in result

    def test_supports_format(self):
        """Test format support."""
        renderer = TemplateRenderer()
        assert renderer.supports_format("text")
        assert renderer.supports_format("term")
        assert not renderer.supports_format("json")
        assert not renderer.supports_format("yaml")

    def test_empty_tree(self):
        """Test rendering empty node."""
        root = Node(label="")
        renderer = TemplateRenderer()
        presentation = Presentation()
        result = renderer.render(root, presentation)

        # Should handle empty label gracefully
        assert "1L" in result

    def test_terminal_width_respected(self):
        """Test that terminal width is respected."""
        root = Node(
            label="A long label that might need truncation", type="paragraph"
        )

        renderer = TemplateRenderer()

        # Test narrow terminal
        narrow_presentation = Presentation()
        narrow_presentation.view.max_width = 30
        narrow = renderer.render(root, narrow_presentation)
        assert len(narrow.split("\n")[0]) <= 30

        # Test wide terminal
        wide_presentation = Presentation()
        wide_presentation.view.max_width = 100
        wide = renderer.render(root, wide_presentation)
        assert len(wide.split("\n")[0]) <= 100

    def test_rich_markup_in_term_mode(self):
        """Test that Rich markup is applied based on terminal detection."""
        root = Node(label="Colored", type="document")

        renderer = TemplateRenderer()

        # The renderer now auto-detects terminal capabilities
        # In pytest environment, sys.stdout.isatty() returns False, so no ANSI codes
        presentation = Presentation()
        result = renderer.render(root, presentation)

        # Check that result doesn't contain ANSI codes in test environment
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        # In test environment, should not have ANSI codes
        assert not ansi_escape.search(
            result
        ), "Found ANSI codes in test environment"

        # Should have plain text content
        assert "⧉ Colored" in result
        assert "1L" in result

    def test_node_with_icon_override(self):
        """Test node with explicit icon override."""
        root = Node(
            label="Custom Icon",
            type="document",
            icon="🌟",  # Override default icon
        )

        renderer = TemplateRenderer()
        presentation = Presentation()
        result = renderer.render(root, presentation)

        # Should use the custom icon
        assert "🌟" in result
        assert "Custom Icon" in result
