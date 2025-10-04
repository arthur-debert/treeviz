"""
Tests for path extraction in collection mapping templates.

This module tests the enhanced template substitution that supports
path expressions in placeholders like ${item.c[0]}.
"""

from treeviz.adapters.extraction.engine import (
    apply_collection_mapping,
    _substitute_template,
    _resolve_placeholder_expression,
)


class TestPathExtractionInTemplates:
    """Test path expression support in collection mapping templates."""

    def test_simple_path_extraction(self):
        """Test basic path extraction in templates."""
        collection = [{"c": "hello", "t": "Str"}, {"c": "world", "t": "Str"}]

        map_spec = {
            "template": {
                "type": "TextNode",
                "content": "${item.c}",
                "node_type": "${item.t}",
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"type": "TextNode", "content": "hello", "node_type": "Str"},
            {"type": "TextNode", "content": "world", "node_type": "Str"},
        ]
        assert result == expected

    def test_array_index_path_extraction(self):
        """Test array index access in path expressions."""
        collection = [
            {"content": ["first", "second", "third"]},
            {"content": ["alpha", "beta"]},
        ]

        map_spec = {
            "template": {
                "first_item": "${item.content[0]}",
                "second_item": "${item.content[1]}",
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"first_item": "first", "second_item": "second"},
            {"first_item": "alpha", "second_item": "beta"},
        ]
        assert result == expected

    def test_nested_object_path_extraction(self):
        """Test nested object access in path expressions."""
        collection = [
            {"metadata": {"author": "Alice", "tags": ["tag1", "tag2"]}},
            {"metadata": {"author": "Bob", "tags": ["tag3"]}},
        ]

        map_spec = {
            "template": {
                "author": "${item.metadata.author}",
                "first_tag": "${item.metadata.tags[0]}",
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"author": "Alice", "first_tag": "tag1"},
            {"author": "Bob", "first_tag": "tag3"},
        ]
        assert result == expected

    def test_pandoc_realistic_example(self):
        """Test realistic Pandoc list item processing."""
        # This represents how Pandoc list items are structured
        pandoc_items = [
            [{"t": "Plain", "c": [{"t": "Str", "c": "Item 1"}]}],
            [{"t": "Plain", "c": [{"t": "Str", "c": "Item 2"}]}],
        ]

        # Now we can extract the text directly in the mapping
        map_spec = {
            "template": {
                "t": "ListItem",
                "text": "${item[0].c[0].c}",  # Direct path to the text content
                "original": "${item}",  # Keep original structure too
            }
        }

        result = apply_collection_mapping(pandoc_items, map_spec)

        expected = [
            {
                "t": "ListItem",
                "text": "Item 1",
                "original": [
                    {"t": "Plain", "c": [{"t": "Str", "c": "Item 1"}]}
                ],
            },
            {
                "t": "ListItem",
                "text": "Item 2",
                "original": [
                    {"t": "Plain", "c": [{"t": "Str", "c": "Item 2"}]}
                ],
            },
        ]
        assert result == expected

    def test_path_expression_with_missing_field(self):
        """Test graceful handling when path doesn't exist."""
        collection = [
            {"name": "test", "data": {"value": 42}},
            {"name": "test2"},  # Missing 'data' field
        ]

        map_spec = {
            "template": {
                "name": "${item.name}",
                "value": "${item.data.value}",  # Will be None for second item
                "fallback": "default",
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {"name": "test", "value": 42, "fallback": "default"},
            {
                "name": "test2",
                "value": None,
                "fallback": "default",
            },  # Failed path returns None for exact match
        ]
        assert result == expected

    def test_mixed_simple_and_path_placeholders(self):
        """Test mixing simple placeholders with path expressions."""
        collection = [
            {"type": "node", "content": {"text": "hello", "length": 5}}
        ]

        map_spec = {
            "template": {
                "node_type": "${item.type}",  # Simple access
                "text": "${item.content.text}",  # Path expression
                "length": "${item.content.length}",  # Path expression
                "debug": "Type: ${item.type}, Text: ${item.content.text}",  # Mixed in string
            }
        }

        result = apply_collection_mapping(collection, map_spec)

        expected = [
            {
                "node_type": "node",
                "text": "hello",
                "length": 5,
                "debug": "Type: node, Text: hello",
            }
        ]
        assert result == expected


class TestTemplateSubstitutionInternals:
    """Test the internal template substitution functions."""

    def test_resolve_placeholder_expression_simple(self):
        """Test simple variable resolution."""
        context = {"item": {"name": "test", "value": 42}}

        result = _resolve_placeholder_expression("item", context)
        assert result == {"name": "test", "value": 42}

    def test_resolve_placeholder_expression_with_path(self):
        """Test path expression resolution."""
        context = {"item": {"data": {"nested": ["a", "b", "c"]}}}

        result = _resolve_placeholder_expression("item.data.nested[1]", context)
        assert result == "b"

    def test_resolve_placeholder_expression_missing_variable(self):
        """Test handling of missing variables."""
        context = {"other": "value"}

        result = _resolve_placeholder_expression("missing.path", context)
        assert result is None

    def test_resolve_placeholder_expression_invalid_path(self):
        """Test handling of invalid paths."""
        context = {"item": {"data": "string"}}

        # Trying to access array index on a string returns the character
        result = _resolve_placeholder_expression("item.data[0]", context)
        assert result == "s"  # First character of "string"

    def test_substitute_template_exact_match_with_path(self):
        """Test exact template match preserves type with path expressions."""
        context = {"item": {"data": {"count": 42}}}

        # Exact match should preserve the integer type
        result = _substitute_template("${item.data.count}", context)
        assert result == 42
        assert isinstance(result, int)

    def test_substitute_template_string_interpolation_with_path(self):
        """Test string interpolation with path expressions."""
        context = {"item": {"name": "test", "value": 100}}

        template = "Name: ${item.name}, Value: ${item.value}"
        result = _substitute_template(template, context)
        assert result == "Name: test, Value: 100"

    def test_substitute_template_nested_structures(self):
        """Test template substitution in nested data structures."""
        context = {"item": {"id": "abc", "props": {"color": "red"}}}

        template = {
            "node_id": "${item.id}",
            "style": {"color": "${item.props.color}", "size": "large"},
            "tags": ["${item.id}", "processed"],
        }

        result = _substitute_template(template, context)

        expected = {
            "node_id": "abc",
            "style": {"color": "red", "size": "large"},
            "tags": ["abc", "processed"],
        }
        assert result == expected


class TestErrorHandling:
    """Test error handling in path extraction."""

    def test_malformed_placeholder(self):
        """Test handling of malformed placeholders."""
        context = {"item": {"data": "test"}}

        # Missing closing brace - should be treated as literal
        result = _substitute_template("${item.data", context)
        assert result == "${item.data"

    def test_empty_placeholder(self):
        """Test handling of empty placeholders."""
        context = {"item": "test"}

        result = _substitute_template("${}", context)
        assert (
            result == ""
        )  # Empty expression resolves to empty string in string context

    def test_complex_path_failure(self):
        """Test complex path that fails partway through."""
        context = {"item": {"data": None}}

        # Path fails at .value because data is None
        result = _substitute_template("${item.data.value}", context)
        assert result is None
