"""
Tests for the declarative converter engine.
"""

import pytest
from treeviz.converter import DeclarativeConverter, ConversionError, convert_tree
from treeviz.model import Node


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_basic_conversion(assert_node):
    """Test basic conversion with simple configuration."""
    config = {"attributes": {"label": "name", "type": "node_type"}}

    source = MockNode(name="Test Node", node_type="test")

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert isinstance(result, Node)
    assert_node(result).has_label("Test Node").has_type("test")


def test_children_conversion(assert_node):
    """Test conversion with children."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        }
    }

    child = MockNode(name="Child", node_type="child")
    parent = MockNode(name="Parent", node_type="parent", child_nodes=[child])

    converter = DeclarativeConverter(config)
    result = converter.convert(parent)

    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Child").has_type("child")


def test_icon_mapping(assert_node):
    """Test icon mapping functionality."""
    config = {
        "attributes": {"label": "name", "type": "node_type"},
        "icon_map": {"paragraph": "¶", "list": "☰"},
    }

    source = MockNode(name="Test", node_type="paragraph")

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_icon("¶")


def test_type_overrides(assert_node):
    """Test type-specific attribute overrides."""
    config = {
        "attributes": {"label": "name", "type": "node_type"},
        "type_overrides": {"text": {"label": "content"}},
    }

    source = MockNode(name="Wrong", content="Correct", node_type="text")

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_label("Correct")


def test_ignore_types(assert_node):
    """Test ignoring specific node types."""
    config = {
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

    converter = DeclarativeConverter(config)
    result = converter.convert(parent)

    # Should only have one child (text), comment should be ignored
    assert_node(result).has_children_count(1)
    assert_node(result.children[0]).has_label("Text")


def test_callable_extractors(assert_node):
    """Test using callable functions as attribute extractors."""
    config = {
        "attributes": {
            "label": lambda node: node.first_name + " " + node.last_name,
            "type": "node_type",
        }
    }

    source = MockNode(first_name="John", last_name="Doe", node_type="person")

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_label("John Doe")


def test_missing_attribute_fallback(assert_node):
    """Test fallback when attribute is missing."""
    config = {"attributes": {"label": "missing_field", "type": "node_type"}}

    source = MockNode(node_type="test")  # missing_field not set

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    # Should fallback to type name
    assert_node(result).has_label("test")


def test_dict_access(assert_node):
    """Test accessing attributes from dictionary nodes."""
    config = {"attributes": {"label": "name", "type": "type"}}

    source = {"name": "Test", "type": "dict_node"}

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_label("Test").has_type("dict_node")


def test_metadata_extraction(assert_node):
    """Test extracting metadata."""
    config = {
        "attributes": {"label": "name", "type": "node_type", "metadata": "meta"}
    }

    source = MockNode(
        name="Test", node_type="test", meta={"key": "value", "count": 42}
    )

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_metadata({"key": "value", "count": 42})


def test_source_location_extraction(assert_node):
    """Test extracting source location information."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "source_location": "location",
        }
    }

    source = MockNode(
        name="Test", node_type="test", location={"line": 5, "column": 10}
    )

    converter = DeclarativeConverter(config)
    result = converter.convert(source)

    assert_node(result).has_source_location({"line": 5, "column": 10})


def test_invalid_configuration():
    """Test that invalid configurations raise errors."""
    # No attributes section
    with pytest.raises(ConversionError, match="must include 'attributes'"):
        DeclarativeConverter({})

    # No label in attributes
    with pytest.raises(
        ConversionError, match="must specify how to extract 'label'"
    ):
        DeclarativeConverter({"attributes": {"type": "node_type"}})


def test_conversion_error_on_bad_children():
    """Test that non-list children cause conversion error."""
    config = {
        "attributes": {
            "label": "name",
            "children": "bad_children",  # This will return a string
        }
    }

    source = MockNode(name="Test", bad_children="not a list")

    converter = DeclarativeConverter(config)
    with pytest.raises(
        ConversionError, match="Children attribute must return a list"
    ):
        converter.convert(source)


def test_convert_tree_convenience_function(assert_node):
    """Test the convert_tree convenience function."""
    config = {"attributes": {"label": "name", "type": "node_type"}}

    source = MockNode(name="Root", node_type="root")

    result = convert_tree(source, config)

    assert isinstance(result, Node)
    assert_node(result).has_label("Root").has_type("root")


def test_convert_tree_with_ignored_root():
    """Test convert_tree when root is ignored."""
    config = {
        "attributes": {"label": "name", "type": "node_type"},
        "ignore_types": ["root"],
    }

    source = MockNode(name="Root", node_type="root")

    with pytest.raises(ConversionError, match="Root node was ignored"):
        convert_tree(source, config)
