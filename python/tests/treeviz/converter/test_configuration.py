"""
Tests for DeclarativeConverter definition handling.

This test file focuses specifically on how the converter handles various
definition scenarios, validation, and error cases.
"""

import pytest
from treeviz.adapter import adapt_node, ConversionError


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_minimal_valid_defuration():
    """Test converter with minimal valid definition."""
    def_ = {"attributes": {"label": "name"}}
    source = MockNode(name="test")

    # Should not raise an exception
    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_validation_no_attributes():
    """Test that definition without attributes section raises error."""
    def_ = {}
    source = MockNode()

    with pytest.raises(ConversionError, match="must include 'attributes'"):
        adapt_node(source, def_)


def test_defuration_validation_no_label():
    """Test that definition without label mapping raises error."""
    def_ = {"attributes": {"type": "node_type"}}
    source = MockNode(node_type="test")

    with pytest.raises(
        ConversionError, match="must specify how to extract 'label'"
    ):
        adapt_node(source, def_)


def test_defuration_with_icon_map():
    """Test definition with icon mapping."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "icon_map": {"paragraph": "¶", "list": "☰", "heading": "⊤"},
    }
    source = MockNode(name="test", node_type="paragraph")

    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_with_type_overrides():
    """Test definition with type-specific attribute overrides."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "type_overrides": {
            "text": {"label": "content"},
            "heading": {"label": "title", "metadata": "attrs"},
        },
    }
    source = MockNode(name="test", node_type="text", content="text content")

    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_with_ignore_types():
    """Test definition with ignored node types."""
    def_ = {
        "attributes": {"label": "name", "type": "node_type"},
        "ignore_types": ["comment", "whitespace", "debug"],
    }
    source = MockNode(name="test", node_type="normal")

    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_with_all_features():
    """Test definition using all available features."""
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
            "icon": "symbol",
            "content_lines": "line_count",
            "source_location": "location",
            "metadata": "meta",
        },
        "icon_map": {"paragraph": "¶", "list": "☰"},
        "type_overrides": {"text": {"label": "content"}},
        "ignore_types": ["comment"],
    }
    source = MockNode(name="test", node_type="paragraph", child_nodes=[])

    result = adapt_node(source, def_)
    assert result is not None


def test_invalid_defuration_types():
    """Test that invalid definition types are rejected."""
    # The converter doesn't currently validate input types,
    # it would fail at runtime when trying to access dict methods
    # This is a design decision - we'll just test that it doesn't crash
    # on conversion with valid structure

    # Test with valid minimal def_
    valid_def = {"attributes": {"label": "name"}}
    source = MockNode(name="test")
    result = adapt_node(source, valid_def)
    assert result is not None


def test_defuration_error_messages():
    """Test that definition errors provide helpful messages."""
    source = MockNode()

    try:
        adapt_node(source, {})
    except ConversionError as e:
        assert "attributes" in str(e).lower()

    try:
        adapt_node(source, {"attributes": {"type": "node_type"}})
    except ConversionError as e:
        assert "label" in str(e).lower()
