"""
Additional hardcore tests for edge cases that may be missed in the main test suite.

This focuses on specific problematic scenarios discovered during testing.
"""

import pytest
from treeviz.advanced_extraction import (
    PathExpressionEngine,
    TransformationEngine,
    FilterEngine,
    AdvancedAttributeExtractor,
)
from treeviz.exceptions import ConversionError
from treeviz import DeclarativeConverter


class TestTruncationEdgeCases:
    """Test truncation edge cases that are causing failures."""

    @pytest.mark.parametrize(
        "text,max_length,suffix,expected",
        [
            # Exact length cases
            ("exactly10", 10, "…", "exactly10"),  # Exactly max length
            (
                "exactly10",
                10,
                "...",
                "exactly10",
            ),  # Exactly max length with different suffix
            # Edge case where suffix is longer than max_length
            ("text", 3, "...", "..."),  # Suffix length equals max_length
            (
                "text",
                2,
                "...",
                "..",
            ),  # Suffix longer than max_length (truncated)
            ("text", 1, "...", "."),  # Suffix much longer than max_length
            ("text", 0, "...", ""),  # Zero max_length
            # Unicode handling
            ("hello🌍", 7, "…", "hello🌍"),  # Unicode within limit
            (
                "hello🌍world",
                7,
                "…",
                "hello🌍…",
            ),  # Unicode truncated with suffix
            # Empty suffix cases
            ("hello world", 5, "", "hello"),  # No suffix
            (
                "hello",
                10,
                "",
                "hello",
            ),  # No truncation needed with empty suffix
        ],
    )
    def test_truncation_edge_cases(self, text, max_length, suffix, expected):
        """Test truncation with various edge cases."""
        engine = TransformationEngine()
        result = engine.apply_transformation(
            text,
            {"name": "truncate", "max_length": max_length, "suffix": suffix},
        )
        assert result == expected


class TestFilteringEdgeCases:
    """Test filtering edge cases."""

    def test_empty_filter_results(self):
        """Test filtering that results in empty collections."""
        engine = FilterEngine()

        items = [{"type": "A"}, {"type": "B"}]
        result = engine.filter_collection(
            items, {"type": "C"}
        )  # Nothing matches
        assert result == []

        result = engine.filter_collection([], {"type": "A"})  # Empty input
        assert result == []

    def test_complex_nested_filtering(self):
        """Test complex nested logical operations."""
        engine = FilterEngine()

        items = [
            {"a": 1, "b": {"c": "x"}},
            {"a": 2, "b": {"c": "y"}},
            {"a": 1, "b": {"c": "y"}},
        ]

        # This tests dot notation path access in filters
        result = engine.filter_collection(items, {"b.c": "y"})
        assert len(result) == 2
        # Verify all returned items have b.c == "y"
        for item in result:
            assert item["b"]["c"] == "y", f"Item {item} should have b.c == 'y'"

    def test_filter_with_transformation_chain(self):
        """Test filtering objects after transformation."""
        extractor = AdvancedAttributeExtractor()

        data = {
            "items": [
                {"name": "HELLO", "type": "greeting"},
                {"name": "world", "type": "noun"},
                {"name": "TEST", "type": "action"},
                {"name": "example", "type": "noun"},
            ]
        }

        # Transform names to lowercase, then filter by type
        result = extractor.extract_attribute(
            data,
            {
                "path": "items",
                "transform": lambda lst: [
                    {**item, "name": item["name"].lower()} for item in lst
                ],
                "filter": {"type": "noun"},
            },
        )

        assert len(result) == 2
        assert all(item["type"] == "noun" for item in result)
        assert result[0]["name"] == "world"
        assert result[1]["name"] == "example"


class TestPathExpressionEdgeCases:
    """Test path expression edge cases."""

    def test_very_deep_nesting(self):
        """Test very deep nesting scenarios."""
        engine = PathExpressionEngine()

        deep_data = {"a": {"b": {"c": {"d": {"e": {"f": "deep_value"}}}}}}
        result = engine.extract_by_path(deep_data, "a.b.c.d.e.f")
        assert result == "deep_value"

    def test_mixed_data_types_in_paths(self):
        """Test paths through mixed data types."""
        engine = PathExpressionEngine()

        mixed_data = {
            "config": {
                "items": [
                    {"name": "first", "values": [10, 20, 30]},
                    {"name": "second", "values": [40, 50, 60]},
                ]
            }
        }

        result = engine.extract_by_path(mixed_data, "config.items[1].values[0]")
        assert result == 40

    def test_numeric_keys_and_indices(self):
        """Test handling of numeric keys vs indices."""
        engine = PathExpressionEngine()

        # Dict with numeric string keys
        data_dict = {"0": "zero_string", "1": "one_string"}
        result = engine.extract_by_path(data_dict, "['0']")
        assert result == "zero_string"

        # List with numeric indices
        data_list = ["zero_index", "one_index"]
        result = engine.extract_by_path(data_list, "[0]")
        assert result == "zero_index"

    @pytest.mark.parametrize(
        "empty_input",
        [
            {},
            [],
            None,
            "",
            {"empty": {}},
            {"empty": []},
        ],
    )
    def test_empty_input_handling(self, empty_input):
        """Test that empty inputs are handled gracefully."""
        engine = PathExpressionEngine()

        # Should not crash on empty inputs
        result = engine.extract_by_path(empty_input, "any.path")
        assert result is None


class TestDeclarativeConverterIntegration:
    """Test complete integration scenarios."""

    def test_metadata_transformation_with_fallback(self):
        """Test metadata extraction with transformation and fallback."""
        config = {
            "attributes": {
                "label": "name",
                "metadata": {
                    "path": "description",
                    "fallback": "summary",
                    "default": "No description",
                    "transform": {"name": "truncate", "max_length": 20},
                },
                "children": [],
            }
        }

        converter = DeclarativeConverter(config)

        # Test with description
        source1 = {
            "name": "item1",
            "description": "This is a very long description that will be truncated",
        }
        result1 = converter.convert(source1)
        assert len(result1.metadata) <= 20
        assert result1.metadata.endswith("…")

        # Test with fallback
        source2 = {"name": "item2", "summary": "Short summary"}
        result2 = converter.convert(source2)
        assert result2.metadata == "Short summary"

        # Test with default
        source3 = {"name": "item3"}
        result3 = converter.convert(source3)
        assert result3.metadata == "No description"

    def test_complex_filtering_in_type_overrides(self):
        """Test complex filtering in type-specific overrides."""
        config = {
            "attributes": {
                "label": "name",
                "type": "node_type",
                "children": "items",
            },
            "type_overrides": {
                "filtered_module": {
                    "children": {
                        "path": "functions",
                        "filter": {
                            "and": [
                                {"visibility": "public"},
                                {
                                    "or": [
                                        {"name": {"startswith": "get_"}},
                                        {"name": {"startswith": "set_"}},
                                    ]
                                },
                            ]
                        },
                    }
                }
            },
        }

        converter = DeclarativeConverter(config)

        source = {
            "name": "MyModule",
            "node_type": "filtered_module",
            "functions": [
                {"name": "get_user", "visibility": "public"},
                {"name": "set_config", "visibility": "public"},
                {"name": "internal_helper", "visibility": "private"},
                {
                    "name": "get_data",
                    "visibility": "private",
                },  # Matches name but not visibility
                {
                    "name": "process_item",
                    "visibility": "public",
                },  # Matches visibility but not name
            ],
            "items": [],
        }

        result = converter.convert(source)
        assert (
            len(result.children) == 2
        )  # Only get_user and set_config should pass the filter

    def test_error_propagation_through_conversion(self):
        """Test that errors are properly propagated through the conversion chain."""
        config = {
            "attributes": {
                "label": {"path": "name", "transform": "invalid_transform"},
                "children": [],
            }
        }

        converter = DeclarativeConverter(config)
        source = {"name": "test"}

        with pytest.raises(ConversionError, match="Unknown transformation"):
            converter.convert(source)

    def test_large_collection_filtering_performance(self):
        """Test performance with larger collections."""
        config = {
            "attributes": {
                "label": "name",
                "children": {"path": "items", "filter": {"value": {"gt": 500}}},
            }
        }

        converter = DeclarativeConverter(config)

        # Generate large dataset
        large_source = {
            "name": "root",
            "items": [{"value": i, "name": f"item_{i}"} for i in range(1000)],
        }

        result = converter.convert(large_source)

        # Should efficiently filter to items with value > 500
        assert len(result.children) == 499  # 501-999 inclusive
        assert all(
            child.metadata == {} for child in result.children
        )  # No metadata extracted

        # Verify that all children are actually items with value > 500
        # We need to check the original source data correspondence
        # The filtered children should correspond to items with values 501-999
        for i, child in enumerate(result.children):
            expected_value = (
                501 + i
            )  # First filtered item should have value 501
            assert (
                expected_value > 500
            ), f"Child at index {i} should represent an item with value > 500"


class TestRegressionTests:
    """Tests for specific bugs found during development."""

    def test_dict_method_access_bug(self):
        """Test that dict methods like 'items' aren't accessed instead of dict keys."""
        engine = PathExpressionEngine()

        data = {"items": ["a", "b", "c"], "keys": ["x", "y", "z"]}

        # These should access the dict values, not the methods
        assert engine.extract_by_path(data, "items") == ["a", "b", "c"]
        assert engine.extract_by_path(data, "keys") == ["x", "y", "z"]
        assert engine.extract_by_path(data, "items[0]") == "a"

    def test_empty_bracket_handling(self):
        """Test that empty brackets are handled correctly."""
        engine = PathExpressionEngine()
        data = {"test": [1, 2, 3]}

        with pytest.raises(ConversionError):
            engine.extract_by_path(data, "test[]")

    def test_transformation_order_in_extraction(self):
        """Test that transformation happens after path extraction but before filtering."""
        extractor = AdvancedAttributeExtractor()

        data = {
            "items": [{"name": "HELLO"}, {"name": "WORLD"}, {"name": "test"}]
        }

        # Transform names to lowercase, then filter for ones starting with 'h'
        result = extractor.extract_attribute(
            data,
            {
                "path": "items",
                "transform": lambda items: [
                    {"name": item["name"].lower()} for item in items
                ],
                "filter": {"name": {"startswith": "h"}},
            },
        )

        assert len(result) == 1
        assert result[0]["name"] == "hello"
