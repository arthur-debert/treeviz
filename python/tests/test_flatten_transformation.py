"""
Tests for the flatten transformation.

This module tests the new flatten transformation that handles
nested list structures common in complex document formats like Pandoc.
"""

import pytest
from treeviz.adapters.extraction.transforms import apply_transformation


class TestFlattenTransformation:
    """Test the flatten transformation."""

    def test_basic_flatten(self):
        """Test basic flattening of nested lists."""
        nested_list = [[1, 2], [3, 4], [5]]

        result = apply_transformation(nested_list, "flatten")

        expected = [1, 2, 3, 4, 5]
        assert result == expected

    def test_flatten_with_depth_parameter(self):
        """Test flattening with specific depth control."""
        nested_list = [[[1, 2]], [[3, 4]], [[5, 6]]]

        # Depth 1: flatten outer level only
        result_depth_1 = apply_transformation(
            nested_list, {"name": "flatten", "depth": 1}
        )
        expected_depth_1 = [[1, 2], [3, 4], [5, 6]]
        assert result_depth_1 == expected_depth_1

        # Depth 2: flatten completely
        result_depth_2 = apply_transformation(
            nested_list, {"name": "flatten", "depth": 2}
        )
        expected_depth_2 = [1, 2, 3, 4, 5, 6]
        assert result_depth_2 == expected_depth_2

    def test_flatten_unlimited_depth(self):
        """Test flattening with unlimited depth."""
        deeply_nested = [[[[[1]], [2]]], [[[3, 4]]]]

        result = apply_transformation(
            deeply_nested, {"name": "flatten", "depth": -1}
        )

        expected = [1, 2, 3, 4]
        assert result == expected

    def test_flatten_mixed_types(self):
        """Test flattening with mixed types including strings."""
        nested_list = [["hello", "world"], [1, 2], ["test"]]

        result = apply_transformation(nested_list, "flatten")

        expected = ["hello", "world", 1, 2, "test"]
        assert result == expected

    def test_flatten_preserves_non_iterable_items(self):
        """Test that non-iterable items are preserved as-is."""
        nested_list = [[1, 2], "string", [3, 4], 42, [None]]

        result = apply_transformation(nested_list, "flatten")

        expected = [1, 2, "string", 3, 4, 42, None]
        assert result == expected

    def test_flatten_empty_lists(self):
        """Test flattening with empty sublists."""
        nested_list = [[1, 2], [], [3], [], [4, 5]]

        result = apply_transformation(nested_list, "flatten")

        expected = [1, 2, 3, 4, 5]
        assert result == expected

    def test_flatten_already_flat_list(self):
        """Test flattening an already flat list."""
        flat_list = [1, 2, 3, 4, 5]

        result = apply_transformation(flat_list, "flatten")

        # Should remain the same
        assert result == flat_list

    def test_flatten_zero_depth(self):
        """Test flattening with depth 0 (no flattening)."""
        nested_list = [[1, 2], [3, 4]]

        result = apply_transformation(
            nested_list, {"name": "flatten", "depth": 0}
        )

        # Should be a copy of the original list
        assert result == nested_list
        assert result is not nested_list  # Should be a copy

    def test_flatten_pandoc_realistic_example(self):
        """Test flattening realistic Pandoc-style nested structures."""
        # This represents a Pandoc structure where list items contain
        # lists of block elements that need to be flattened
        pandoc_structure = [
            [
                {"t": "Para", "c": [{"t": "Str", "c": "Item 1"}]},
                {"t": "Para", "c": [{"t": "Str", "c": "Continued"}]},
            ],
            [{"t": "Para", "c": [{"t": "Str", "c": "Item 2"}]}],
        ]

        result = apply_transformation(pandoc_structure, "flatten")

        expected = [
            {"t": "Para", "c": [{"t": "Str", "c": "Item 1"}]},
            {"t": "Para", "c": [{"t": "Str", "c": "Continued"}]},
            {"t": "Para", "c": [{"t": "Str", "c": "Item 2"}]},
        ]
        assert result == expected

    def test_flatten_in_pipeline(self):
        """Test flatten as part of a transformation pipeline."""
        nested_data = [
            [
                {"type": "text", "value": "hello"},
                {"type": "text", "value": "world"},
            ],
            [{"type": "punct", "value": "!"}],
            [{"type": "text", "value": "test"}],
        ]

        # Pipeline: flatten then filter then extract values
        pipeline = [
            {"name": "flatten"},
            {"name": "filter", "type": "text"},
            {"name": "extract", "field": "value"},
            {"name": "join", "separator": " "},
        ]

        result = apply_transformation(nested_data, pipeline)

        expected = "hello world test"
        assert result == expected

    def test_flatten_error_cases(self):
        """Test error handling for invalid inputs."""
        # Non-iterable input
        with pytest.raises(
            ValueError, match="flatten transformation requires iterable"
        ):
            apply_transformation(42, "flatten")

        # String input (should be rejected)
        with pytest.raises(
            ValueError, match="flatten transformation requires iterable"
        ):
            apply_transformation("string", "flatten")

        # Invalid depth type
        with pytest.raises(
            ValueError, match="flatten transformation requires integer depth"
        ):
            apply_transformation(
                [[1, 2]], {"name": "flatten", "depth": "invalid"}
            )

    def test_flatten_nested_tuples(self):
        """Test flattening with nested tuples."""
        nested_tuples = [(1, 2), (3, 4), (5,)]

        result = apply_transformation(nested_tuples, "flatten")

        expected = [1, 2, 3, 4, 5]
        assert result == expected

    def test_flatten_complex_mixed_nesting(self):
        """Test flattening complex mixed nested structures."""
        complex_structure = [[1, [2, 3]], 4, [[5], 6], [7, [8, [9]]]]

        # Depth 1
        result_1 = apply_transformation(
            complex_structure, {"name": "flatten", "depth": 1}
        )
        expected_1 = [1, [2, 3], 4, [5], 6, 7, [8, [9]]]
        assert result_1 == expected_1

        # Unlimited depth
        result_unlimited = apply_transformation(
            complex_structure, {"name": "flatten", "depth": -1}
        )
        expected_unlimited = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert result_unlimited == expected_unlimited
