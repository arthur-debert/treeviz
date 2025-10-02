"""
Tests for DeclarativeConverter tree processing functionality.

This test file focuses on how the converter handles tree structures,
children processing, and hierarchical data conversion.
"""

import pytest
from treeviz.converter import (
    DeclarativeConverter,
    ConversionError,
    convert_tree,
)
from treeviz.model import Node


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_single_node_conversion(assert_node):
    """Test conversion of a single node without children."""
    config = {"attributes": {"label": "name", "type": "node_type"}}
    source = MockNode(name="Leaf Node", node_type="leaf")

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_label("Leaf Node").has_type(
        "leaf"
    ).has_children_count(0)


def test_parent_child_conversion(assert_node):
    """Test conversion of parent node with children."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    child1 = MockNode(name="Child 1", node_type="child")
    child2 = MockNode(name="Child 2", node_type="child")
    parent = MockNode(
        name="Parent", node_type="parent", child_nodes=[child1, child2]
    )

    converter = DeclarativeConverter(config)
    result = converter.convert(parent)

    assert_node(result).has_label("Parent").has_type(
        "parent"
    ).has_children_count(2)
    assert_node(result.children[0]).has_label("Child 1").has_type("child")
    assert_node(result.children[1]).has_label("Child 2").has_type("child")


def test_deep_tree_conversion(assert_node):
    """Test conversion of deeply nested tree structures."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    # Create a 3-level deep tree
    grandchild = MockNode(name="Grandchild", node_type="leaf")
    child = MockNode(name="Child", node_type="branch", child_nodes=[grandchild])
    root = MockNode(name="Root", node_type="root", child_nodes=[child])

    converter = DeclarativeConverter(config)
    result = converter.convert(root)

    # Test the full tree structure
    assert_node(result).has_label("Root").has_type("root").has_children_count(1)

    child_result = result.children[0]
    assert_node(child_result).has_label("Child").has_type(
        "branch"
    ).has_children_count(1)

    grandchild_result = child_result.children[0]
    assert_node(grandchild_result).has_label("Grandchild").has_type(
        "leaf"
    ).has_children_count(0)


def test_empty_children_list(assert_node):
    """Test conversion when children list is empty."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    source = MockNode(name="Empty Parent", node_type="parent", child_nodes=[])

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_children_count(0)


def test_missing_children_attribute(assert_node):
    """Test conversion when children attribute is missing."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "missing_children",
        }
    }

    source = MockNode(name="No Children", node_type="parent")

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_children_count(0)


def test_children_conversion_error():
    """Test error when children attribute returns non-list."""
    config = {
        "attributes": {
            "label": "name",
            "children": "bad_children",
        }
    }

    source = MockNode(name="Bad Parent", bad_children="not a list")

    converter = DeclarativeConverter(config)
    with pytest.raises(
        ConversionError, match="Children attribute must return a list"
    ):
        converter.convert(source)


def test_mixed_child_types(assert_node):
    """Test conversion with children of different types."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    text_child = MockNode(name="Text Content", node_type="text")
    list_child = MockNode(name="List", node_type="list", child_nodes=[])
    heading_child = MockNode(name="Heading", node_type="heading")

    parent = MockNode(
        name="Document",
        node_type="document",
        child_nodes=[heading_child, text_child, list_child],
    )

    converter = DeclarativeConverter(config)
    result = converter.convert(parent)

    assert_node(result).has_children_count(3)
    assert_node(result.children[0]).has_type("heading")
    assert_node(result.children[1]).has_type("text")
    assert_node(result.children[2]).has_type("list")


def test_convert_tree_convenience_function(assert_node):
    """Test the convert_tree convenience function."""
    config = {"attributes": {"label": "name", "type": "node_type"}}
    source = MockNode(name="Root", node_type="root")

    result = convert_tree(source, config)

    assert isinstance(result, Node)
    assert_node(result).has_label("Root").has_type("root")


def test_convert_tree_with_children(assert_node):
    """Test convert_tree with complex tree structure."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    child = MockNode(name="Child", node_type="child")
    parent = MockNode(name="Parent", node_type="parent", child_nodes=[child])

    result = convert_tree(parent, config)

    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Child")


def test_recursive_tree_processing():
    """Test that tree processing handles recursive structures correctly."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    # Create a tree where each level has multiple children
    leaf1 = MockNode(name="Leaf 1", node_type="leaf")
    leaf2 = MockNode(name="Leaf 2", node_type="leaf")
    branch1 = MockNode(name="Branch 1", node_type="branch", child_nodes=[leaf1])
    branch2 = MockNode(name="Branch 2", node_type="branch", child_nodes=[leaf2])
    root = MockNode(
        name="Root", node_type="root", child_nodes=[branch1, branch2]
    )

    converter = DeclarativeConverter(config)
    result = converter.convert(root)

    # Verify the complete tree structure
    assert len(result.children) == 2
    assert len(result.children[0].children) == 1
    assert len(result.children[1].children) == 1
    assert len(result.children[0].children[0].children) == 0
    assert len(result.children[1].children[0].children) == 0
