"""
Tests for collection mapping feature in the extraction engine.

This module tests the ability to transform collections using templates,
which is essential for Pandoc list processing.
"""

import pytest
from treeviz.adapters.extraction.engine import (
    apply_collection_mapping,
    extract_attribute,
)


class TestCollectionMapping:
    """Test collection mapping functionality."""

    def test_simple_mapping(self):
        """Test basic collection mapping with template."""
        collection = ["a", "b", "c"]
        map_spec = {
            "template": {"t": "ListItem", "c": "${item}"},
            "variable": "item",
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"t": "ListItem", "c": "a"},
            {"t": "ListItem", "c": "b"},
            {"t": "ListItem", "c": "c"},
        ]
        assert result == expected

    def test_default_variable_name(self):
        """Test that default variable name 'item' works."""
        collection = [1, 2, 3]
        map_spec = {"template": {"value": "${item}"}}

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"value": 1},  # Exact placeholder preserves type
            {"value": 2},
            {"value": 3},
        ]
        assert result == expected

    def test_custom_variable_name(self):
        """Test collection mapping with custom variable name."""
        collection = ["x", "y"]
        map_spec = {
            "template": {"id": "${element}", "type": "node"},
            "variable": "element",
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [{"id": "x", "type": "node"}, {"id": "y", "type": "node"}]
        assert result == expected

    def test_nested_template_structure(self):
        """Test mapping with nested template structures."""
        collection = [{"name": "Alice"}, {"name": "Bob"}]
        map_spec = {
            "template": {
                "t": "Person",
                "data": {"original": "${item}", "processed": True},
            },
            "variable": "item",
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {
                "t": "Person",
                "data": {"original": {"name": "Alice"}, "processed": True},
            },
            {
                "t": "Person",
                "data": {"original": {"name": "Bob"}, "processed": True},
            },
        ]
        assert result == expected

    def test_template_with_list(self):
        """Test template containing lists."""
        collection = ["item1", "item2"]
        map_spec = {"template": {"content": ["${item}"], "metadata": []}}

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"content": ["item1"], "metadata": []},
            {"content": ["item2"], "metadata": []},
        ]
        assert result == expected

    def test_multiple_placeholders(self):
        """Test template with multiple instances of the same placeholder."""
        collection = ["test"]
        map_spec = {
            "template": {
                "id": "${item}",
                "name": "${item}",
                "backup": "${item}",
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [{"id": "test", "name": "test", "backup": "test"}]
        assert result == expected

    def test_empty_collection(self):
        """Test mapping with empty collection."""
        collection = []
        map_spec = {"template": {"t": "Item", "c": "${item}"}}

        result = apply_collection_mapping(collection, map_spec)
        assert result == []

    def test_complex_item_objects(self):
        """Test mapping with complex objects as items."""
        collection = [
            {"type": "paragraph", "text": "Hello"},
            {"type": "header", "level": 1, "text": "Title"},
        ]
        map_spec = {
            "template": {
                "t": "Node",
                "original": "${item}",
                "id": "node_${item}",
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        # ${item} as exact match preserves object, but in string context becomes string
        assert len(result) == 2
        assert all(item["t"] == "Node" for item in result)
        assert (
            result[0]["original"] == collection[0]
        )  # Exact match preserves object
        assert (
            result[0]["id"] == "node_{'type': 'paragraph', 'text': 'Hello'}"
        )  # String context

    def test_pandoc_bullet_list_example(self):
        """Test realistic Pandoc BulletList mapping example."""
        # This mimics the Pandoc BulletList children structure
        pandoc_items = [
            [{"t": "Plain", "c": [{"t": "Str", "c": "Item 1"}]}],
            [{"t": "Plain", "c": [{"t": "Str", "c": "Item 2"}]}],
        ]

        map_spec = {
            "template": {"t": "ListItem", "c": "${item}"},
            "variable": "item",
        }

        result = apply_collection_mapping(pandoc_items, map_spec)

        expected = [
            {
                "t": "ListItem",
                "c": [{"t": "Plain", "c": [{"t": "Str", "c": "Item 1"}]}],
            },
            {
                "t": "ListItem",
                "c": [{"t": "Plain", "c": [{"t": "Str", "c": "Item 2"}]}],
            },
        ]
        assert result == expected

    def test_error_cases(self):
        """Test various error conditions."""
        # Non-list input
        with pytest.raises(
            ValueError, match="Collection mapping requires list input"
        ):
            apply_collection_mapping("not a list", {"template": {}})

        # Invalid map_spec type
        with pytest.raises(ValueError, match="Map specification must be dict"):
            apply_collection_mapping([], "not a dict")

        # Missing template
        with pytest.raises(
            ValueError, match="Map specification must include 'template' field"
        ):
            apply_collection_mapping([], {"variable": "item"})

    def test_non_string_placeholders(self):
        """Test that non-string template values are preserved."""
        collection = [42, 3.14]
        map_spec = {
            "template": {
                "value": "${item}",  # Exact placeholder preserves type
                "count": 1,
                "active": True,
                "data": None,
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {
                "value": 42,
                "count": 1,
                "active": True,
                "data": None,
            },  # Preserves int
            {
                "value": 3.14,
                "count": 1,
                "active": True,
                "data": None,
            },  # Preserves float
        ]
        assert result == expected


class TestCollectionMappingIntegration:
    """Test collection mapping integrated with full extraction pipeline."""

    def test_extraction_with_mapping(self):
        """Test complete extraction pipeline including mapping."""
        source_node = {
            "type": "BulletList",
            "items": ["First item", "Second item", "Third item"],
        }

        extraction_spec = {
            "path": "items",
            "map": {
                "template": {"t": "ListItem", "content": "${item}"},
                "variable": "item",
            },
        }

        result = extract_attribute(source_node, extraction_spec)

        expected = [
            {"t": "ListItem", "content": "First item"},
            {"t": "ListItem", "content": "Second item"},
            {"t": "ListItem", "content": "Third item"},
        ]
        assert result == expected

    def test_transform_then_map(self):
        """Test transformation followed by mapping."""
        source_node = {"data": "a,b,c"}

        extraction_spec = {
            "path": "data",
            "transform": [
                {"name": "str"},  # Ensure string
                {"name": "upper"},  # Convert to uppercase
            ],
            "map": {"template": {"t": "Letter", "value": "${item}"}},
        }

        # This should log a warning and return the string as-is because map expects a list
        # but transform returns string
        result = extract_attribute(source_node, extraction_spec)
        assert result == "A,B,C"  # The transformed string, mapping was skipped

    def test_filter_then_map(self):
        """Test filtering followed by mapping."""
        source_node = {
            "nodes": [
                {"type": "text", "content": "hello"},
                {"type": "image", "src": "pic.jpg"},
                {"type": "text", "content": "world"},
            ]
        }

        extraction_spec = {
            "path": "nodes",
            "transform": {"name": "filter", "type": "text"},
            "map": {"template": {"t": "TextNode", "original": "${item}"}},
        }

        result = extract_attribute(source_node, extraction_spec)

        assert len(result) == 2
        assert all(item["t"] == "TextNode" for item in result)
        assert result[0]["original"]["content"] == "hello"
        assert result[1]["original"]["content"] == "world"
