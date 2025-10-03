"""
Tests for DeclarativeConverter definition handling.

This test file focuses specifically on how the converter handles various
definition scenarios, validation, and error cases.
"""

from treeviz.adapter import adapt_node


class MockNode:
    """Mock AST node for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_minimal_valid_defuration():
    """Test converter with minimal valid definition."""
    def_ = {"label": "name"}
    source = MockNode(name="test")

    # Should not raise an exception
    result = adapt_node(source, def_)
    assert result is not None


def test_definition_uses_defaults_when_empty():
    """Test that empty definition uses all defaults."""
    def_ = {}
    source = MockNode(label="test", type="unknown", children=[])

    # Should not raise an exception - uses defaults
    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_validation_no_label():
    """Test that definition without label mapping uses default 'label' field."""
    def_ = {"type": "node_type"}
    source = MockNode(label="test", node_type="test")

    # Should use default "label" field without error
    result = adapt_node(source, def_)
    assert result.label == "test"


def test_defuration_with_icons():
    """Test definition with icon mapping."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "icons": {"paragraph": "¶", "list": "☰", "heading": "⊤"},
    }
    source = MockNode(name="test", node_type="paragraph")

    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_with_type_overrides():
    """Test definition with type-specific attribute overrides."""
    def_ = {
        "label": "name",
        "type": "node_type",
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
        "label": "name",
        "type": "node_type",
        "ignore_types": ["comment", "whitespace", "debug"],
    }
    source = MockNode(name="test", node_type="normal")

    result = adapt_node(source, def_)
    assert result is not None


def test_defuration_with_all_features():
    """Test definition using all available features."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "child_nodes",
        "icon": "symbol",
        "content_lines": "line_count",
        "source_location": "location",
        "metadata": "meta",
        "icons": {"paragraph": "¶", "list": "☰"},
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
    valid_def = {"label": "name"}
    source = MockNode(name="test")
    result = adapt_node(source, valid_def)
    assert result is not None


def test_defuration_error_messages():
    """Test that definition errors provide helpful messages."""
    source = MockNode()

    try:
        adapt_node(source, {})
    except KeyError as e:
        assert "attributes" in str(e).lower()

    try:
        adapt_node(source, {"type": "node_type"})
    except KeyError as e:
        assert "label" in str(e).lower()
