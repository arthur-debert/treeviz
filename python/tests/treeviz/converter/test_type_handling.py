"""
Tests for DeclarativeConverter type handling functionality.

This test file focuses on type-specific behavior including type overrides,
icon mapping, and ignored types.
"""

import pytest
from treeviz.adapter import adapt_node


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_iconsping_basic(assert_node):
    """Test basic icon mapping functionality."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "icons": {"paragraph": "¶", "list": "☰", "heading": "⊤"},
    }

    source = MockNode(name="Paragraph", node_type="paragraph")

    # Using functional API
    result = adapt_node(source, def_)

    assert_node(result).has_icon("¶")


def test_iconsping_missing_type():
    """Test icon mapping when type is not in map."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "icons": {"paragraph": "¶"},
    }

    source = MockNode(name="Unknown", node_type="unknown")

    # Using functional API
    result = adapt_node(source, def_)

    # Should get fallback icon from baseline const.py
    assert result.icon == "?"


def test_iconsping_multiple_types():
    """Test icon mapping with various node types."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "icons": {
            "document": "⧉",
            "paragraph": "¶",
            "list": "☰",
            "text": "◦",
            "code": "ƒ",
        },
    }

    test_cases = [
        ("Document", "document", "⧉"),
        ("Text", "text", "◦"),
        ("Code Block", "code", "ƒ"),
    ]

    # Using functional API

    for name, node_type, expected_icon in test_cases:
        source = MockNode(name=name, node_type=node_type)
        result = adapt_node(source, def_)
        assert result.icon == expected_icon


def test_type_overrides_simple(assert_node):
    """Test simple type-specific attribute overrides."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "type_overrides": {"text": {"label": "content"}},
    }

    source = MockNode(name="Wrong", content="Correct", node_type="text")

    # Using functional API
    result = adapt_node(source, def_)

    assert_node(result).has_label("Correct")


def test_type_overrides_multiple_attributes(assert_node):
    """Test type overrides affecting multiple attributes."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "metadata": "default_meta",
        "type_overrides": {
            "special": {"label": "title", "metadata": "special_meta"}
        },
    }

    source = MockNode(
        name="Wrong Name",
        title="Correct Title",
        node_type="special",
        default_meta={"default": True},
        special_meta={"special": True},
    )

    # Using functional API
    result = adapt_node(source, def_)

    assert_node(result).has_label("Correct Title").has_metadata(
        {"special": True}
    )


def test_type_overrides_multiple_types():
    """Test type overrides for multiple different types."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "type_overrides": {
            "text": {"label": "content"},
            "heading": {"label": "title"},
            "code": {"label": "code_content"},
        },
    }

    # Using functional API

    # Test text type
    text_source = MockNode(
        name="Wrong", content="Text Content", node_type="text"
    )
    text_result = adapt_node(text_source, def_)
    assert text_result.label == "Text Content"

    # Test heading type
    heading_source = MockNode(
        name="Wrong", title="Heading Title", node_type="heading"
    )
    heading_result = adapt_node(heading_source, def_)
    assert heading_result.label == "Heading Title"


def test_ignore_types_single(assert_node):
    """Test ignoring a single node type."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "child_nodes",
        "ignore_types": ["comment"],
    }

    comment = MockNode(name="Comment", node_type="comment")
    text = MockNode(name="Text", node_type="text")
    parent = MockNode(
        name="Parent", node_type="parent", child_nodes=[comment, text]
    )

    # Using functional API
    result = adapt_node(parent, def_)

    # Should only have one child (text), comment should be ignored
    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Text")


def test_ignore_types_multiple(assert_node):
    """Test ignoring multiple node types."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "child_nodes",
        "ignore_types": ["comment", "whitespace", "debug"],
    }

    comment = MockNode(name="Comment", node_type="comment")
    whitespace = MockNode(name="Whitespace", node_type="whitespace")
    debug = MockNode(name="Debug", node_type="debug")
    text = MockNode(name="Text", node_type="text")

    parent = MockNode(
        name="Parent",
        node_type="parent",
        child_nodes=[comment, text, whitespace, debug],
    )

    # Using functional API
    result = adapt_node(parent, def_)

    # Should only have one child (text)
    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Text")


def test_ignore_types_nested_trees(assert_node):
    """Test that ignored types work in nested tree structures."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "child_nodes",
        "ignore_types": ["comment"],
    }

    # Create nested structure with comments at different levels
    comment1 = MockNode(name="Comment 1", node_type="comment")
    text1 = MockNode(name="Text 1", node_type="text")
    comment2 = MockNode(name="Comment 2", node_type="comment")
    text2 = MockNode(name="Text 2", node_type="text")

    branch = MockNode(
        name="Branch", node_type="branch", child_nodes=[comment1, text1]
    )

    root = MockNode(
        name="Root", node_type="root", child_nodes=[branch, comment2, text2]
    )

    # Using functional API
    result = adapt_node(root, def_)

    # Root should have 2 children (branch and text2)
    assert_node(result).has_children_count(2)

    # Branch should have 1 child (text1)
    branch_result = result.children[0]
    assert_node(branch_result).has_children_count(1)
    assert_node(branch_result.children[0]).has_label("Text 1")


def test_adapt_tree_with_ignored_root():
    """Test error when root node type is ignored."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "ignore_types": ["root"],
    }

    from treeviz.adapter import adapt_tree

    source = MockNode(name="Root", node_type="root")

    with pytest.raises(ValueError, match="Root node was ignored"):
        adapt_tree(source, def_)


def test_combined_type_features(assert_node):
    """Test combining icon mapping, type overrides, and ignore types."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "child_nodes",
        "icons": {"paragraph": "¶", "heading": "⊤"},
        "type_overrides": {"heading": {"label": "title"}},
        "ignore_types": ["comment"],
    }

    comment = MockNode(name="Comment", node_type="comment")
    heading = MockNode(name="Wrong", title="Heading", node_type="heading")
    paragraph = MockNode(name="Paragraph", node_type="paragraph")

    parent = MockNode(
        name="Parent",
        node_type="parent",
        child_nodes=[comment, heading, paragraph],
    )

    # Using functional API
    result = adapt_node(parent, def_)

    # Should have 2 children (heading and paragraph, comment ignored)
    assert_node(result).has_children_count(2)

    # Check heading with override and icon
    heading_result = result.children[0]
    assert_node(heading_result).has_label("Heading").has_icon("⊤")

    # Check paragraph with icon
    paragraph_result = result.children[1]
    assert_node(paragraph_result).has_label("Paragraph").has_icon("¶")
