"""
Tests for basic rendering functionality.

This test file focuses on core rendering behavior, output formatting,
and basic tree structure rendering using the functional interface.
"""

from treeviz.rendering import TemplateRenderer
from treeviz.model import Node

# Create a module-level renderer instance for all tests
renderer = TemplateRenderer()


def test_render_single_node():
    """Test rendering a single node without children."""
    node = Node(type="text", label="Hello World")

    output = renderer.render(node)

    assert "◦ Hello World" in output
    assert output.count("\n") == 0  # Single line


def test_render_node_with_custom_icon():
    """Test rendering node with custom icon mapping."""
    node = Node(type="paragraph", label="Test paragraph")

    output = renderer.render(node)

    assert "¶ Test paragraph" in output


def test_render_node_with_unknown_type():
    """Test rendering node with unknown type uses default icon."""
    node = Node(type="unknown", label="Unknown node")

    output = renderer.render(node)

    assert "? Unknown node" in output


def test_render_simple_tree():
    """Test rendering a simple tree with parent and children."""
    child1 = Node(type="text", label="Child 1")
    child2 = Node(type="text", label="Child 2")
    parent = Node(type="paragraph", label="Parent", children=[child1, child2])

    output = renderer.render(parent)

    lines = output.split("\n")
    assert "¶ Parent" in lines[0]
    assert "  ◦ Child 1" in lines[1]  # Indented
    assert "  ◦ Child 2" in lines[2]  # Indented


def test_render_deep_tree():
    """Test rendering a deeply nested tree structure."""
    grandchild = Node(type="text", label="Grandchild")
    child = Node(type="paragraph", label="Child", children=[grandchild])
    root = Node(type="document", label="Root", children=[child])

    output = renderer.render(root)

    lines = output.split("\n")
    assert "⧉ Root" in lines[0]
    assert "  ¶ Child" in lines[1]
    assert "    ◦ Grandchild" in lines[2]


def test_render_empty_tree():
    """Test rendering a node with empty children list."""
    node = Node(type="document", label="Empty Document", children=[])

    output = renderer.render(node)

    # Should contain the symbol and label
    assert "⧉ Empty Document" in output
    assert "1L" in output  # Line count for single line content


def test_render_output_format():
    """Test that rendered output has correct format and structure."""
    child = Node(type="text", label="Text content")
    parent = Node(type="document", label="Document", children=[child])

    output = renderer.render(parent)

    # Check basic structure - symbols are present
    assert "⧉ Document" in output
    assert "◦ Text content" in output
    # Parent should show child count, child should show line count
    assert "1L" in output  # For child line count


def test_render_multiple_children():
    """Test rendering node with multiple children of different types."""
    children = [
        Node(type="heading", label="Heading"),
        Node(type="paragraph", label="Paragraph"),
        Node(type="list", label="List"),
        Node(type="text", label="Text"),
    ]
    parent = Node(type="document", label="Document", children=children)

    output = renderer.render(parent)

    lines = output.split("\n")
    assert len(lines) == 5  # Parent + 4 children
    assert "⧉ Document" in lines[0]
    assert "⊤ Heading" in lines[1]
    assert "¶ Paragraph" in lines[2]
    assert "☰ List" in lines[3]
    assert "◦ Text" in lines[4]


def test_render_preserves_label_content():
    """Test that rendering preserves exact label content."""
    special_labels = [
        "Label with spaces",
        "Label-with-dashes",
        "Label_with_underscores",
        "Label.with.dots",
        "Label (with parentheses)",
        "Label [with brackets]",
        "Label {with braces}",
        "Label/with/slashes",
        "Label\\with\\backslashes",
    ]

    for label in special_labels:
        node = Node(type="text", label=label)
        output = renderer.render(node)
        assert label in output


def test_render_unicode_labels():
    """Test rendering with Unicode characters in labels."""
    unicode_labels = [
        "Café",
        "naïve",
        "résumé",
        "北京",
        "🚀 Rocket",
        "α + β = γ",
    ]

    for label in unicode_labels:
        node = Node(type="text", label=label)
        output = renderer.render(node)
        assert label in output


def test_render_newlines_in_output():
    """Test that output contains correct number of newlines."""
    # Single node - no newlines
    single = Node(type="text", label="Single")
    output = renderer.render(single)
    assert "\n" not in output

    # Parent with one child - one newline
    child = Node(type="text", label="Child")
    parent = Node(type="paragraph", label="Parent", children=[child])
    output = renderer.render(parent)
    assert output.count("\n") == 1

    # Parent with two children - two newlines
    child1 = Node(type="text", label="Child 1")
    child2 = Node(type="text", label="Child 2")
    parent = Node(type="paragraph", label="Parent", children=[child1, child2])
    output = renderer.render(parent)
    assert output.count("\n") == 2
