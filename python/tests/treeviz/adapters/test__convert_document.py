"""
Unit tests for convert_document function.

Tests the document conversion functionality using existing adapt_node.
"""

import pytest
from unittest.mock import patch

from treeviz.adapters.utils import convert_document
from treeviz.model import Node


class TestConvertDocument:
    """Test cases for convert_document function."""

    def test_convert_document_basic(self):
        """Test basic document conversion."""
        document = {"name": "test_node", "type": "function", "children": []}

        adapter_def = {"label": "name", "type": "type", "children": "children"}

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "test_node"
        assert result.type == "function"
        assert result.children == []

    def test_convert_document_with_nested_structure(self):
        """Test conversion with nested document structure."""
        document = {
            "title": "root",
            "kind": "document",
            "items": [
                {"title": "child1", "kind": "section"},
                {"title": "child2", "kind": "paragraph"},
            ],
        }

        adapter_def = {"label": "title", "type": "kind", "children": "items"}

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "root"
        assert result.type == "document"
        assert len(result.children) == 2
        assert result.children[0].label == "child1"
        assert result.children[0].type == "section"
        assert result.children[1].label == "child2"
        assert result.children[1].type == "paragraph"

    def test_convert_document_with_icons(self):
        """Test conversion with icon mapping."""
        document = {"name": "test_func", "type": "function"}

        adapter_def = {
            "label": "name",
            "type": "type",
            "icons": {"function": "⚡", "class": "🏛️"},
        }

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "test_func"
        assert result.type == "function"
        assert result.icon == "⚡"

    def test_convert_document_delegates_to_adapt_node(self):
        """Test that convert_document properly delegates to adapt_node."""
        document = {"test": "data"}
        adapter_def = {"label": "test"}

        with patch("treeviz.adapters.core.adapt_node") as mock_adapt_node:
            expected_result = Node(label="test_result")
            mock_adapt_node.return_value = expected_result

            result = convert_document(document, adapter_def)

            # Should have called adapt_node with the right arguments
            mock_adapt_node.assert_called_once_with(document, adapter_def)
            assert result == expected_result

    def test_convert_document_preserves_adapt_node_errors(self):
        """Test that convert_document preserves errors from adapt_node."""
        document = {"invalid": "structure"}
        adapter_def = {"missing_required_fields": True}

        # This should raise an exception from adapt_node
        with pytest.raises(
            Exception
        ):  # Could be KeyError, TypeError, ValueError, etc.
            convert_document(document, adapter_def)

    def test_convert_document_with_complex_mapping(self):
        """Test conversion with complex field mappings."""
        document = {
            "metadata": {"display_name": "Complex Node", "node_type": "custom"},
            "content": {
                "line_count": 5,
                "source_info": {"line": 10, "column": 5},
            },
            "child_elements": [
                {"metadata": {"display_name": "Child", "node_type": "item"}}
            ],
        }

        adapter_def = {
            "label": "metadata.display_name",
            "type": "metadata.node_type",
            "content_lines": "content.line_count",
            "source_location": "content.source_info",
            "children": "child_elements",
        }

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "Complex Node"
        assert result.type == "custom"
        assert result.content_lines == 5
        assert result.source_location == {"line": 10, "column": 5}
        assert len(result.children) == 1
        assert result.children[0].label == "Child"

    def test_convert_document_with_type_overrides(self):
        """Test conversion with type-specific overrides."""
        document = {
            "name": "special_node",
            "type": "special",
            "extra_field": "special_value",
        }

        adapter_def = {
            "label": "name",
            "type": "type",
            "type_overrides": {"special": {"label": "extra_field"}},
        }

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "special_value"  # Should use override
        assert result.type == "special"

    def test_convert_document_with_ignore_types(self):
        """Test conversion with ignored node types."""
        document = {"name": "comment_node", "type": "comment"}

        adapter_def = {
            "label": "name",
            "type": "type",
            "ignore_types": ["comment", "whitespace"],
        }

        result = convert_document(document, adapter_def)

        # Should return None for ignored types
        assert result is None

    def test_convert_document_with_all_fields(self):
        """Test conversion using all possible Node fields."""
        document = {
            "title": "Full Node",
            "node_type": "complete",
            "icon_symbol": "🌟",
            "line_count": 10,
            "location": {"line": 15, "column": 8},
            "metadata": {"author": "test", "version": "1.0"},
            "children": [],
        }

        adapter_def = {
            "label": "title",
            "type": "node_type",
            "icon": "icon_symbol",
            "content_lines": "line_count",
            "source_location": "location",
            "extra": "metadata",
            "children": "children",
        }

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "Full Node"
        assert result.type == "complete"
        assert result.icon == "🌟"
        assert result.content_lines == 10
        assert result.source_location == {"line": 15, "column": 8}
        assert result.extra == {"author": "test", "version": "1.0"}
        assert result.children == []


class TestConvertDocumentIntegration:
    """Integration tests for convert_document with real data."""

    def test_convert_document_json_structure(self):
        """Test converting a typical JSON document structure."""
        document = {
            "type": "document",
            "children": [
                {
                    "type": "paragraph",
                    "children": [{"type": "text", "value": "Hello world"}],
                },
                {
                    "type": "heading",
                    "depth": 1,
                    "children": [{"type": "text", "value": "Title"}],
                },
            ],
        }

        # MDAST-like adapter definition
        adapter_def = {
            "label": "value",
            "type": "type",
            "children": "children",
            "icons": {
                "document": "⧉",
                "paragraph": "¶",
                "heading": "⊤",
                "text": "◦",
            },
        }

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.type == "document"
        assert result.icon == "⧉"
        assert len(result.children) == 2

        # Check paragraph
        paragraph = result.children[0]
        assert paragraph.type == "paragraph"
        assert paragraph.icon == "¶"
        assert len(paragraph.children) == 1
        assert paragraph.children[0].label == "Hello world"

        # Check heading
        heading = result.children[1]
        assert heading.type == "heading"
        assert heading.icon == "⊤"
        assert len(heading.children) == 1
        assert heading.children[0].label == "Title"

    def test_convert_document_with_minimal_definition(self):
        """Test conversion with minimal adapter definition."""
        document = {"name": "simple_node"}

        # Minimal definition - other fields should get defaults
        adapter_def = {"label": "name"}

        result = convert_document(document, adapter_def)

        assert isinstance(result, Node)
        assert result.label == "simple_node"
        assert result.type is None  # No type field in document
        assert result.children == []  # Default empty list
