"""
Tests for the declarative converter engine.
"""

import pytest
from treeviz.adapter import (
    adapt_tree,
    adapt_node,
)
from treeviz.model import Node


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_basic_conversion(assert_node):
    """Test basic conversion with simple definition."""
    def_ = {"attributes": {"label": "name", "type": "node_type"}}

    source = MockNode(name="Test Node", node_type="test")

    result = adapt_node(source, def_)

    assert isinstance(result, Node)
    assert_node(result).has_label("Test Node").has_type("test")


def test_children_conversion(assert_node):
    """Test conversion with children."""
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    child = MockNode(name="Child", node_type="child")
    parent = MockNode(name="Parent", node_type="parent", child_nodes=[child])

    result = adapt_node(parent, def_)

    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Child").has_type("child")


def test_iconsping(assert_node):
    """Test icon mapping functionality."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "icons": {"paragraph": "¶", "list": "☰"},
    }

    source = MockNode(name="Test", node_type="paragraph")

    result = adapt_node(source, def_)

    assert_node(result).has_icon("¶")


def test_type_overrides(assert_node):
    """Test type-specific attribute overrides."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "type_overrides": {"text": {"label": "content"}},
    }

    source = MockNode(name="Wrong", content="Correct", node_type="text")

    result = adapt_node(source, def_)

    assert_node(result).has_label("Correct")


def test_ignore_types(assert_node):
    """Test ignoring specific node types."""
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        },
        "ignore_types": ["comment"],
    }

    comment = MockNode(name="Comment", node_type="comment")
    text = MockNode(name="Text", node_type="text")
    parent = MockNode(
        name="Parent", node_type="parent", child_nodes=[comment, text]
    )

    result = adapt_node(parent, def_)

    # Should only have one child (text), comment should be ignored
    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Text")


def test_callable_extractors(assert_node):
    """Test using callable functions as attribute extractors."""
    def_ = {
        "attributes": {
            "label": lambda node: node.first_name + " " + node.last_name,
            "type": "node_type",
        }
    }

    source = MockNode(first_name="John", last_name="Doe", node_type="person")

    result = adapt_node(source, def_)

    assert_node(result).has_label("John Doe")


def test_missing_attribute_fallback(assert_node):
    """Test fallback when attribute is missing."""
    def_ = {"attributes": {"label": "missing_field", "type": "node_type"}}

    source = MockNode(node_type="test")  # missing_field not set

    result = adapt_node(source, def_)

    # Should fallback to type name
    assert_node(result).has_label("test")


def test_dict_access(assert_node):
    """Test accessing attributes from dictionary nodes."""
    def_ = {"attributes": {"label": "name", "type": "type"}}

    source = {"name": "Test", "type": "dict_node"}

    result = adapt_node(source, def_)

    assert_node(result).has_label("Test").has_type("dict_node")


def test_metadata_extraction(assert_node):
    """Test extracting metadata."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type", "metadata": "meta"}
    }

    source = MockNode(
        name="Test", node_type="test", meta={"key": "value", "count": 42}
    )

    result = adapt_node(source, def_)

    assert_node(result).has_metadata({"key": "value", "count": 42})


def test_source_location_extraction(assert_node):
    """Test extracting source location information."""
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "source_location": "location",
        }
    }

    source = MockNode(
        name="Test", node_type="test", location={"line": 5, "column": 10}
    )

    result = adapt_node(source, def_)

    assert_node(result).has_source_location({"line": 5, "column": 10})


def test_invalid_defuration():
    """Test that invalid definitions raise errors."""
    # Empty definition should work (uses defaults)
    source = {"label": "test", "type": "test"}
    result = adapt_node(source, {})
    assert result is not None

    # No label in attributes should fail
    with pytest.raises(KeyError, match="must specify how to extract 'label'"):
        adapt_node({}, {"attributes": {"type": "node_type"}})


def test_conversion_error_on_bad_children():
    """Test that non-list children cause conversion error."""
    def_ = {
        "attributes": {
            "label": "name",
            "children": "bad_children",  # This will return a string
        }
    }

    source = MockNode(name="Test", bad_children="not a list")

    with pytest.raises(
        TypeError, match="Children attribute must return a list"
    ):
        adapt_node(source, def_)


def test_adapt_tree_convenience_function(assert_node):
    """Test the adapt_tree convenience function."""
    def_ = {"attributes": {"label": "name", "type": "node_type"}}

    source = MockNode(name="Root", node_type="root")

    result = adapt_tree(source, def_)

    assert isinstance(result, Node)
    assert_node(result).has_label("Root").has_type("root")


def test_adapt_tree_with_ignored_root():
    """Test adapt_tree when root is ignored."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "ignore_types": ["root"],
    }

    source = MockNode(name="Root", node_type="root")

    with pytest.raises(ValueError, match="Root node was ignored"):
        adapt_tree(source, def_)


# Tests for the new functional API
def test_adapt_node_basic(assert_node):
    """Test basic conversion with adapt_node function."""
    def_ = {"attributes": {"label": "name", "type": "node_type"}}

    source = MockNode(name="Test Node", node_type="test")

    result = adapt_node(source, def_)

    assert isinstance(result, Node)
    assert_node(result).has_label("Test Node").has_type("test")


def test_adapt_node_with_children(assert_node):
    """Test conversion with children using adapt_node function."""
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    child = MockNode(name="Child", node_type="child")
    parent = MockNode(name="Parent", node_type="parent", child_nodes=[child])

    result = adapt_node(parent, def_)

    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Child").has_type("child")


def test_adapt_node_ignored_type():
    """Test adapt_node returns None for ignored types."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "ignore_types": ["comment"],
    }

    source = MockNode(name="Comment", node_type="comment")

    result = adapt_node(source, def_)

    assert result is None
