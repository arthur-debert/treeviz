"""
Tests for DeclarativeConverter attribute extraction functionality.

This test file focuses on how the converter extracts various attributes
from source nodes using different extraction methods.
"""

from treeviz.adapter import adapt_node


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_basic_attribute_extraction(assert_node):
    """Test basic attribute extraction from object properties."""
    def_ = {"label": "name", "type": "node_type"}
    source = MockNode(name="Test Node", node_type="test")

    result = adapt_node(source, def_)

    assert_node(result).has_label("Test Node").has_type("test")


def test_dict_attribute_extraction(assert_node):
    """Test attribute extraction from dictionary-like objects."""
    def_ = {"label": "name", "type": "type"}
    source = {"name": "Dict Node", "type": "dict_node"}

    result = adapt_node(source, def_)

    assert_node(result).has_label("Dict Node").has_type("dict_node")


def test_callable_attribute_extraction(assert_node):
    """Test attribute extraction using callable functions."""
    def_ = {
        "label": lambda node: f"{node.first_name} {node.last_name}",
        "type": "node_type",
    }
    source = MockNode(first_name="John", last_name="Doe", node_type="person")

    result = adapt_node(source, def_)

    assert_node(result).has_label("John Doe").has_type("person")


def test_missing_attribute_fallback(assert_node):
    """Test fallback behavior when attributes are missing."""
    def_ = {"label": "name", "type": "node_type"}
    source = MockNode(node_type="test")  # name field not present

    result = adapt_node(source, def_)

    # Should fallback to node_type for missing label
    assert_node(result).has_label("test").has_type("test")


def test_content_lines_extraction(assert_node):
    """Test extraction of content_lines attribute."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "content_lines": "line_count",
    }
    source = MockNode(name="Multi-line", node_type="block", line_count=5)

    result = adapt_node(source, def_)

    assert_node(result).has_content_lines(5)


def test_content_lines_fallback(assert_node):
    """Test fallback when content_lines is not a valid integer."""
    def_ = {"label": "name", "type": "type"}
    source = MockNode(name="Test", invalid_lines="not-a-number")

    result = adapt_node(source, def_)

    # Should fallback to 1 when invalid
    assert_node(result).has_content_lines(1)


def test_metadata_extraction(assert_node):
    """Test extraction of metadata attribute."""
    def_ = {"label": "name", "type": "node_type", "metadata": "meta"}
    metadata = {"key": "value", "count": 42, "nested": {"inner": "data"}}
    source = MockNode(name="Test", node_type="test", meta=metadata)

    result = adapt_node(source, def_)

    assert_node(result).has_metadata(metadata)


def test_source_location_extraction(assert_node):
    """Test extraction of source location information."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "source_location": "location",
    }
    location = {"line": 10, "column": 5, "file": "test.py"}
    source = MockNode(name="Test", node_type="test", location=location)

    result = adapt_node(source, def_)

    assert_node(result).has_source_location(location)


def test_icon_extraction_from_attribute():
    """Test extraction of icon from node attribute."""
    def_ = {"label": "name", "type": "node_type", "icon": "symbol"}
    source = MockNode(name="Test", node_type="test", symbol="★")

    result = adapt_node(source, def_)

    assert result.icon == "★"


def test_complex_nested_extraction(assert_node):
    """Test extraction from deeply nested object structures."""
    def_ = {
        "label": lambda node: node.metadata.title,
        "type": "node_type",
        "content_lines": lambda node: len(node.content.lines),
    }

    class NestedNode:
        def __init__(self):
            self.node_type = "nested"
            self.metadata = type("obj", (object,), {"title": "Nested Title"})()
            self.content = type(
                "obj", (object,), {"lines": ["line1", "line2", "line3"]}
            )()

    source = NestedNode()

    result = adapt_node(source, def_)

    assert_node(result).has_label("Nested Title").has_type(
        "nested"
    ).has_content_lines(3)
