"""
Tests for transform pipelines feature in the extraction engine.

This module tests the ability to apply multiple transformations sequentially,
which is essential for complex AST processing like Pandoc.
"""

import pytest
from treeviz.adapters.extraction.transforms import apply_transformation


class TestTransformPipelines:
    """Test transform pipeline functionality."""

    def test_simple_pipeline(self):
        """Test basic pipeline with string transformations."""
        value = "  hello world  "
        pipeline = ["strip", "upper"]

        result = apply_transformation(value, pipeline)
        assert result == "HELLO WORLD"

    def test_collection_pipeline(self):
        """Test pipeline with collection operations."""
        value = ["apple", "banana", "cherry"]
        pipeline = [{"name": "join", "separator": ", "}, "upper"]

        result = apply_transformation(value, pipeline)
        assert result == "APPLE, BANANA, CHERRY"

    def test_complex_pandoc_pipeline(self):
        """Test pipeline that mimics Pandoc text extraction."""
        # Simulate Pandoc AST nodes with mixed types
        pandoc_nodes = [
            {"t": "Str", "c": "Hello"},
            {"t": "Space"},
            {"t": "Str", "c": "world"},
            {"t": "SoftBreak"},
            {"t": "Str", "c": "test"},
        ]

        pipeline = [
            {"name": "filter", "t": "Str"},  # Keep only Str nodes
            {"name": "extract", "field": "c"},  # Extract 'c' field
            {"name": "join", "separator": " "},  # Join with spaces
            {"name": "truncate", "max_length": 10, "suffix": "..."},  # Truncate
        ]

        result = apply_transformation(pandoc_nodes, pipeline)
        assert result == "Hello w..."

    def test_pipeline_with_none_handling(self):
        """Test that None values terminate pipeline gracefully."""
        pipeline = ["strip", "upper"]

        result = apply_transformation(None, pipeline)
        assert result is None

    def test_pipeline_step_returns_none(self):
        """Test pipeline termination when intermediate step returns None."""
        value = "test"
        # Create a pipeline where first step might return None
        pipeline = [
            {"name": "truncate", "max_length": 0},  # This returns empty string
            "upper",  # This should still execute
        ]

        result = apply_transformation(value, pipeline)
        assert result == ""

    def test_empty_pipeline(self):
        """Test empty pipeline returns original value."""
        value = "test"
        pipeline = []

        result = apply_transformation(value, pipeline)
        assert result == "test"

    def test_single_item_pipeline(self):
        """Test pipeline with single transformation."""
        value = "test"
        pipeline = ["upper"]

        result = apply_transformation(value, pipeline)
        assert result == "TEST"

    def test_numeric_pipeline(self):
        """Test pipeline with numeric transformations."""
        value = -3.7
        pipeline = ["abs", {"name": "round", "digits": 0}, "int"]

        result = apply_transformation(value, pipeline)
        assert result == 4

    def test_pipeline_error_propagation(self):
        """Test that errors in pipeline steps are properly propagated."""
        value = "test"
        pipeline = ["strip", {"name": "unknown_transform"}]

        with pytest.raises(
            ValueError, match="Unknown transformation 'unknown_transform'"
        ):
            apply_transformation(value, pipeline)

    def test_mixed_transform_types_in_pipeline(self):
        """Test pipeline mixing different transform specification types."""
        value = "  hello  "
        pipeline = [
            "strip",  # String spec
            {"name": "upper"},  # Dict spec
            lambda x: x + "!",  # Callable spec
        ]

        result = apply_transformation(value, pipeline)
        assert result == "HELLO!"


class TestNewTransformations:
    """Test new transformations added for Pandoc support."""

    def test_prefix_transformation(self):
        """Test prefix transformation."""
        result = apply_transformation(
            "world", {"name": "prefix", "prefix": "hello "}
        )
        assert result == "hello world"

    def test_extract_transformation(self):
        """Test extract transformation for Pandoc nodes."""
        nodes = [
            {"t": "Str", "c": "hello"},
            {"t": "Space"},  # No 'c' field
            {"t": "Str", "c": "world"},
        ]

        result = apply_transformation(nodes, {"name": "extract", "field": "c"})
        assert result == ["hello", None, "world"]

    def test_filter_transformation(self):
        """Test filter transformation for Pandoc nodes."""
        nodes = [
            {"t": "Str", "c": "hello"},
            {"t": "Space"},
            {"t": "Str", "c": "world"},
        ]

        result = apply_transformation(nodes, {"name": "filter", "t": "Str"})
        assert len(result) == 2
        assert all(node["t"] == "Str" for node in result)

    def test_extract_from_objects(self):
        """Test extract transformation with object attributes."""

        class MockNode:
            def __init__(self, value):
                self.content = value

        nodes = [MockNode("hello"), MockNode("world")]
        result = apply_transformation(
            nodes, {"name": "extract", "field": "content"}
        )
        assert result == ["hello", "world"]

    def test_filter_multiple_conditions(self):
        """Test filter with multiple conditions."""
        nodes = [
            {"type": "text", "lang": "en", "content": "hello"},
            {"type": "text", "lang": "fr", "content": "bonjour"},
            {"type": "code", "lang": "en", "content": "print()"},
        ]

        result = apply_transformation(
            nodes, {"name": "filter", "type": "text", "lang": "en"}
        )
        assert len(result) == 1
        assert result[0]["content"] == "hello"
