"""
Integration tests for 3viz Phase 2 enhanced declarative conversion.

These tests verify that the Phase 2 advanced extraction features work correctly
when integrated with the main DeclarativeConverter.
"""

import pytest
from treeviz.adapter import adapt_node
from treeviz.exceptions import ConversionError


class TestPhase2Integration:
    """Test Phase 2 features integrated with DeclarativeConverter."""

    def test_complex_path_expressions_in_def(self):
        """Test complex path expressions in declarative definition."""
        def_ = {
            "attributes": {
                "label": "metadata.title",
                "type": "node_info.type",
                "children": "child_nodes",
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "metadata": {"title": "Test Node"},
            "node_info": {"type": "container"},
            "child_nodes": [],
        }

        result = adapt_node(source_data, def_)
        assert result.label == "Test Node"
        assert result.type == "container"

    def test_fallback_extraction_in_def(self):
        """Test fallback chains in declarative definition."""
        def_ = {
            "attributes": {
                "label": {
                    "path": "title",
                    "fallback": "name",
                    "default": "Untitled",
                },
                "children": "child_nodes",
            }
        }

        # No need for converter instance with functional API

        # Test primary path exists
        source_data = {"title": "Primary Title", "child_nodes": []}
        result = adapt_node(source_data, def_)
        assert result.label == "Primary Title"

        # Test fallback path used
        source_data = {"name": "Fallback Name", "child_nodes": []}
        result = adapt_node(source_data, def_)
        assert result.label == "Fallback Name"

        # Test default value used
        source_data = {"child_nodes": []}
        result = adapt_node(source_data, def_)
        assert result.label == "Untitled"

    def test_transformations_in_def(self):
        """Test transformation functions in declarative definition."""
        def_ = {
            "attributes": {
                "label": {"path": "name", "transform": "upper"},
                "metadata": {
                    "path": "description",
                    "transform": {"name": "truncate", "max_length": 20},
                },
                "children": "child_nodes",
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "name": "test function",
            "description": "This is a very long description that should be truncated",
            "child_nodes": [],
        }

        result = adapt_node(source_data, def_)
        assert result.label == "TEST FUNCTION"
        assert len(result.metadata) <= 20  # Should be truncated

    def test_children_filtering_in_def(self):
        """Test children filtering in declarative definition."""
        def_ = {
            "attributes": {
                "label": "name",
                "children": {
                    "path": "child_nodes",
                    "filter": {"type": {"not_in": ["comment", "whitespace"]}},
                },
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "name": "Parent",
            "child_nodes": [
                {"name": "Child 1", "type": "function", "child_nodes": []},
                {"name": "Comment", "type": "comment", "child_nodes": []},
                {"name": "Child 2", "type": "variable", "child_nodes": []},
                {"name": "Whitespace", "type": "whitespace", "child_nodes": []},
            ],
        }

        result = adapt_node(source_data, def_)
        assert len(result.children) == 2
        assert result.children[0].label == "Child 1"
        assert result.children[1].label == "Child 2"

    def test_type_overrides_with_phase2_features(self):
        """Test type overrides combined with Phase 2 features."""
        def_ = {
            "attributes": {
                "label": "name",
                "type": "node_type",
                "children": "child_nodes",
            },
            "type_overrides": {
                "function": {
                    "label": {
                        "path": "signature",
                        "fallback": "name",
                        "transform": {"name": "truncate", "max_length": 30},
                    },
                    "metadata": {
                        "path": "parameters",
                        "transform": lambda params: {
                            "param_count": len(params) if params else 0
                        },
                    },
                },
                "class": {
                    "label": {"path": "class_name", "transform": "capitalize"}
                },
            },
        }

        # No need for converter instance with functional API

        # Test function with long signature
        function_data = {
            "name": "my_function",
            "node_type": "function",
            "signature": "my_very_long_function_signature_that_should_be_truncated",
            "parameters": ["arg1", "arg2", "arg3"],
            "child_nodes": [],
        }

        result = adapt_node(function_data, def_)
        assert len(result.label) <= 30
        assert result.metadata["param_count"] == 3

        # Test class with transformation
        class_data = {
            "name": "ignored",
            "node_type": "class",
            "class_name": "myclass",
            "child_nodes": [],
        }

        result = adapt_node(class_data, def_)
        assert result.label == "Myclass"

    def test_complex_nested_extraction(self):
        """Test complex nested data extraction with Phase 2 features."""
        def_ = {
            "attributes": {
                "label": {
                    "path": "definition.name",
                    "fallback": "metadata.identifier",
                    "default": "Anonymous",
                },
                "content_lines": "source.line_count",
                "metadata": {
                    "path": "annotations",
                    "transform": lambda anns: {
                        "annotation_count": len(anns) if anns else 0
                    },
                },
                "children": {
                    "path": "body.statements",
                    "filter": {"visibility": {"ne": "private"}},
                },
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "definition": {"name": "PublicClass"},
            "source": {"line_count": 50},
            "annotations": ["@public", "@documented"],
            "body": {
                "statements": [
                    {
                        "name": "public_method",
                        "visibility": "public",
                        "body": {"statements": []},
                    },
                    {
                        "name": "_private_method",
                        "visibility": "private",
                        "body": {"statements": []},
                    },
                    {
                        "name": "protected_method",
                        "visibility": "protected",
                        "body": {"statements": []},
                    },
                ]
            },
        }

        result = adapt_node(source_data, def_)
        assert result.label == "PublicClass"
        assert result.content_lines == 50
        assert result.metadata["annotation_count"] == 2
        assert len(result.children) == 2  # Private method filtered out

    def test_array_indexing_in_def(self):
        """Test array indexing in definition paths."""
        def_ = {
            "attributes": {
                "label": "items[0].name",
                "type": "items[-1].type",
                "children": "child_nodes",
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "items": [
                {"name": "First Item", "type": "start"},
                {"name": "Middle Item", "type": "middle"},
                {"name": "Last Item", "type": "end"},
            ],
            "child_nodes": [],
        }

        result = adapt_node(source_data, def_)
        assert result.label == "First Item"
        assert result.type == "end"

    def test_filtering_with_logical_operators(self):
        """Test complex filtering with logical operators."""
        def_ = {
            "attributes": {
                "label": "name",
                "children": {
                    "path": "members",
                    "filter": {
                        "and": [
                            {"type": "method"},
                            {"visibility": "public"},
                            {"name": {"startswith": "get_"}},
                        ]
                    },
                },
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "name": "APIClass",
            "members": [
                {
                    "name": "get_user",
                    "type": "method",
                    "visibility": "public",
                    "members": [],
                },
                {
                    "name": "get_data",
                    "type": "method",
                    "visibility": "private",
                    "members": [],
                },
                {
                    "name": "set_value",
                    "type": "method",
                    "visibility": "public",
                    "members": [],
                },
                {
                    "name": "get_def",
                    "type": "method",
                    "visibility": "public",
                    "members": [],
                },
                {
                    "name": "internal_var",
                    "type": "variable",
                    "visibility": "public",
                    "members": [],
                },
            ],
        }

        result = adapt_node(source_data, def_)
        assert (
            len(result.children) == 2
        )  # Only get_user and get_def match all conditions
        assert all("get_" in child.label for child in result.children)

    def test_custom_transformation_functions(self):
        """Test custom transformation functions in definition."""

        def format_signature(params):
            if not params:
                return "no_params"
            return f"params({len(params)})"

        def_ = {
            "attributes": {
                "label": "name",
                "metadata": {
                    "path": "parameters",
                    "transform": format_signature,
                },
                "children": "child_nodes",
            }
        }

        # No need for converter instance with functional API

        source_data = {
            "name": "test_function",
            "parameters": ["arg1", "arg2"],
            "child_nodes": [],
        }

        result = adapt_node(source_data, def_)
        assert result.metadata == "params(2)"

    def test_phase2_backward_compatibility(self):
        """Test that Phase 1 definitions still work with Phase 2 converter."""
        # Simple Phase 1 definition
        def_ = {
            "attributes": {
                "label": "name",
                "type": "node_type",
                "children": "child_nodes",
            },
            "icons": {"function": "⚡", "class": "🏛"},
        }

        # No need for converter instance with functional API

        source_data = {
            "name": "test_function",
            "node_type": "function",
            "child_nodes": [],
        }

        result = adapt_node(source_data, def_)
        assert result.label == "test_function"
        assert result.type == "function"
        assert result.icon == "⚡"

    def test_error_handling_in_phase2_features(self):
        """Test proper error handling with Phase 2 features."""
        def_ = {
            "attributes": {
                "label": {
                    "path": "broken[syntax",  # Malformed path
                },
                "children": "child_nodes",
            }
        }

        # No need for converter instance with functional API

        source_data = {"test": "value", "child_nodes": []}

        with pytest.raises(
            ConversionError, match="Failed to evaluate path expression"
        ):
            adapt_node(source_data, def_)
