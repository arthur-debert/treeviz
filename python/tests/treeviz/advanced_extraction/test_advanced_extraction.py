"""
Tests for 3viz Phase 2 advanced extraction features.

These tests cover the enhanced declarative extraction capabilities including
complex path expressions, transformations, filtering, and fallback chains.
"""

import pytest
from treeviz.advanced_extraction import (
    PathExpressionEngine,
    TransformationEngine,
    FilterEngine,
    AdvancedAttributeExtractor,
)
from treeviz.exceptions import ConversionError


class TestPathExpressionEngine:
    """Test complex path expression parsing and evaluation."""

    def test_simple_attribute_access(self):
        """Test basic attribute access."""
        engine = PathExpressionEngine()

        # Object with attributes
        class TestObj:
            name = "test_value"

        obj = TestObj()
        result = engine.extract_by_path(obj, "name")
        assert result == "test_value"

    def test_dict_access(self):
        """Test dictionary-style access."""
        engine = PathExpressionEngine()
        data = {"title": "Test Title", "nested": {"value": 42}}

        result = engine.extract_by_path(data, "title")
        assert result == "Test Title"

    def test_dot_notation(self):
        """Test nested dot notation access."""
        engine = PathExpressionEngine()
        data = {"config": {"database": {"host": "localhost"}}}

        result = engine.extract_by_path(data, "config.database.host")
        assert result == "localhost"

    def test_array_indexing(self):
        """Test array indexing with positive and negative indices."""
        engine = PathExpressionEngine()
        data = {"items": ["first", "second", "third"]}

        # Positive indexing
        result = engine.extract_by_path(data, "items[0]")
        assert result == "first"

        # Negative indexing
        result = engine.extract_by_path(data, "items[-1]")
        assert result == "third"

    def test_complex_path_expressions(self):
        """Test complex nested path expressions."""
        engine = PathExpressionEngine()
        data = {
            "users": [
                {"name": "Alice", "settings": {"theme": "dark"}},
                {"name": "Bob", "settings": {"theme": "light"}},
            ]
        }

        result = engine.extract_by_path(data, "users[0].name")
        assert result == "Alice"

        result = engine.extract_by_path(data, "users[1].settings.theme")
        assert result == "light"

    def test_missing_path_returns_none(self):
        """Test that missing paths return None rather than raising errors."""
        engine = PathExpressionEngine()
        data = {"existing": "value"}

        result = engine.extract_by_path(data, "missing")
        assert result is None

        result = engine.extract_by_path(data, "existing.missing")
        assert result is None

    def test_malformed_path_raises_error(self):
        """Test that malformed path expressions raise ConversionError."""
        engine = PathExpressionEngine()
        data = {"test": "value"}

        with pytest.raises(
            ConversionError, match="Failed to evaluate path expression"
        ):
            engine.extract_by_path(data, "test[malformed")

    def test_bracket_notation_with_string_keys(self):
        """Test bracket notation with string keys."""
        engine = PathExpressionEngine()
        data = {"complex-key": "value", "items": {"another-key": "nested"}}

        result = engine.extract_by_path(data, "['complex-key']")
        assert result == "value"

        result = engine.extract_by_path(data, "items['another-key']")
        assert result == "nested"


class TestTransformationEngine:
    """Test transformation functions and custom transformations."""

    def test_text_transformations(self):
        """Test built-in text transformation functions."""
        engine = TransformationEngine()

        assert engine.apply_transformation("hello", "upper") == "HELLO"
        assert engine.apply_transformation("HELLO", "lower") == "hello"
        assert (
            engine.apply_transformation("hello world", "capitalize")
            == "Hello world"
        )
        assert engine.apply_transformation("  spaced  ", "strip") == "spaced"

    def test_truncate_transformation(self):
        """Test text truncation with configurable parameters."""
        engine = TransformationEngine()

        # Default truncation
        result = engine.apply_transformation(
            "This is a very long text that should be truncated",
            {"name": "truncate", "max_length": 20},
        )
        assert len(result) <= 20
        assert result.endswith("…")

        # Custom suffix
        result = engine.apply_transformation(
            "Long text", {"name": "truncate", "max_length": 5, "suffix": "..."}
        )
        assert result == "Lo..."

    def test_numeric_transformations(self):
        """Test numeric transformation functions."""
        engine = TransformationEngine()

        assert engine.apply_transformation(-5, "abs") == 5
        assert (
            engine.apply_transformation(3.14159, {"name": "round", "digits": 2})
            == 3.14
        )
        assert (
            engine.apply_transformation(
                42, {"name": "format", "format_spec": "04d"}
            )
            == "0042"
        )

    def test_collection_transformations(self):
        """Test collection transformation functions."""
        engine = TransformationEngine()

        items = ["a", "b", "c"]
        assert engine.apply_transformation(items, "length") == 3
        assert (
            engine.apply_transformation(
                items, {"name": "join", "separator": "-"}
            )
            == "a-b-c"
        )
        assert engine.apply_transformation(items, "first") == "a"
        assert engine.apply_transformation(items, "last") == "c"

    def test_custom_transformation_function(self):
        """Test custom transformation functions."""
        engine = TransformationEngine()

        def count_words(text):
            return len(str(text).split())

        result = engine.apply_transformation("hello world test", count_words)
        assert result == 3

    def test_transformation_with_none_value(self):
        """Test that None values skip transformation."""
        engine = TransformationEngine()

        result = engine.apply_transformation(None, "upper")
        assert result is None

    def test_unknown_transformation_raises_error(self):
        """Test that unknown transformations raise ConversionError."""
        engine = TransformationEngine()

        with pytest.raises(ConversionError, match="Unknown transformation"):
            engine.apply_transformation("test", "unknown_transform")


class TestFilterEngine:
    """Test collection filtering with complex predicates."""

    def test_simple_equality_filter(self):
        """Test simple equality-based filtering."""
        engine = FilterEngine()
        items = [
            {"type": "function", "name": "foo"},
            {"type": "class", "name": "Bar"},
            {"type": "function", "name": "baz"},
        ]

        result = engine.filter_collection(items, {"type": "function"})
        assert len(result) == 2
        assert all(item["type"] == "function" for item in result)

    def test_membership_filter(self):
        """Test membership-based filtering."""
        engine = FilterEngine()
        items = [
            {"type": "function"},
            {"type": "class"},
            {"type": "comment"},
            {"type": "variable"},
        ]

        result = engine.filter_collection(
            items, {"type": {"in": ["function", "class"]}}
        )
        assert len(result) == 2
        assert all(item["type"] in ["function", "class"] for item in result)

    def test_string_operation_filters(self):
        """Test string-based filtering operations."""
        engine = FilterEngine()
        items = [
            {"name": "get_user"},
            {"name": "set_value"},
            {"name": "calculate_total"},
            {"name": "update_status"},
        ]

        # Test startswith
        result = engine.filter_collection(
            items, {"name": {"startswith": "get_"}}
        )
        assert len(result) == 1
        assert result[0]["name"] == "get_user"

        # Test contains
        result = engine.filter_collection(items, {"name": {"contains": "calc"}})
        assert len(result) == 1
        assert result[0]["name"] == "calculate_total"

    def test_comparison_filters(self):
        """Test comparison-based filtering."""
        engine = FilterEngine()
        items = [
            {"priority": 1},
            {"priority": 5},
            {"priority": 10},
            {"priority": 15},
        ]

        result = engine.filter_collection(items, {"priority": {"gt": 5}})
        assert len(result) == 2
        assert all(item["priority"] > 5 for item in result)

        result = engine.filter_collection(items, {"priority": {"lte": 5}})
        assert len(result) == 2
        assert all(item["priority"] <= 5 for item in result)

    def test_logical_operators(self):
        """Test logical AND/OR operations in filters."""
        engine = FilterEngine()
        items = [
            {"type": "function", "visibility": "public", "name": "get_data"},
            {"type": "function", "visibility": "private", "name": "helper"},
            {"type": "class", "visibility": "public", "name": "Manager"},
            {"type": "function", "visibility": "public", "name": "set_data"},
        ]

        # Test AND condition
        result = engine.filter_collection(
            items, {"and": [{"type": "function"}, {"visibility": "public"}]}
        )
        assert len(result) == 2
        assert all(
            item["type"] == "function" and item["visibility"] == "public"
            for item in result
        )

        # Test OR condition
        result = engine.filter_collection(
            items, {"or": [{"type": "class"}, {"name": {"startswith": "get_"}}]}
        )
        assert len(result) == 2
        # Verify that each result item matches at least one of the OR conditions
        for item in result:
            matches_condition = item["type"] == "class" or item[
                "name"
            ].startswith("get_")
            assert (
                matches_condition
            ), f"Item {item} should match either type=class or name starts with get_"

    def test_regex_pattern_filter(self):
        """Test regex pattern matching in filters."""
        engine = FilterEngine()
        items = [
            {"name": "test_function_one"},
            {"name": "test_function_two"},
            {"name": "helper_method"},
            {"name": "test_class"},
        ]

        result = engine.filter_collection(
            items, {"name": {"matches": r"test_function_\w+"}}
        )
        assert len(result) == 2
        assert all("test_function_" in item["name"] for item in result)

    def test_type_check_filters(self):
        """Test type checking filters."""
        engine = FilterEngine()
        items = [
            {"value": "string"},
            {"value": 42},
            {"value": None},
            {"value": [1, 2, 3]},
        ]

        result = engine.filter_collection(items, {"value": {"is_none": True}})
        assert len(result) == 1
        assert result[0]["value"] is None

        result = engine.filter_collection(items, {"value": {"type": "str"}})
        assert len(result) == 1
        assert result[0]["value"] == "string"


class TestAdvancedAttributeExtractor:
    """Test the main advanced extraction orchestrator."""

    def test_backward_compatibility_simple_path(self):
        """Test that simple string paths still work (Phase 1 compatibility)."""
        extractor = AdvancedAttributeExtractor()
        data = {"name": "test_value"}

        result = extractor.extract_attribute(data, "name")
        assert result == "test_value"

    def test_backward_compatibility_callable(self):
        """Test that callable extractors still work (Phase 1 compatibility)."""
        extractor = AdvancedAttributeExtractor()
        data = {"items": [1, 2, 3]}

        def get_count(node):
            return len(node["items"])

        result = extractor.extract_attribute(data, get_count)
        assert result == 3

    def test_fallback_chain_extraction(self):
        """Test extraction with fallback paths and default values."""
        extractor = AdvancedAttributeExtractor()
        data = {"backup_name": "fallback_value"}

        result = extractor.extract_attribute(
            data,
            {
                "path": "primary_name",
                "fallback": "backup_name",
                "default": "default_value",
            },
        )
        assert result == "fallback_value"

        # Test default when both paths fail
        result = extractor.extract_attribute(
            data,
            {
                "path": "missing_primary",
                "fallback": "missing_backup",
                "default": "default_value",
            },
        )
        assert result == "default_value"

    def test_extraction_with_transformation(self):
        """Test extraction combined with transformations."""
        extractor = AdvancedAttributeExtractor()
        data = {"title": "hello world"}

        result = extractor.extract_attribute(
            data, {"path": "title", "transform": "upper"}
        )
        assert result == "HELLO WORLD"

    def test_extraction_with_filtering(self):
        """Test extraction with collection filtering."""
        extractor = AdvancedAttributeExtractor()
        data = {
            "items": [
                {"type": "visible", "name": "item1"},
                {"type": "hidden", "name": "item2"},
                {"type": "visible", "name": "item3"},
            ]
        }

        result = extractor.extract_attribute(
            data, {"path": "items", "filter": {"type": "visible"}}
        )
        assert len(result) == 2
        assert all(item["type"] == "visible" for item in result)

    def test_complex_extraction_chain(self):
        """Test complex extraction with multiple features combined."""
        extractor = AdvancedAttributeExtractor()
        data = {
            "metadata": {
                "functions": [
                    {"name": "private_helper", "visibility": "private"},
                    {"name": "public_api", "visibility": "public"},
                    {"name": "internal_util", "visibility": "private"},
                ]
            }
        }

        # Test filtering only (realistic use case)
        result = extractor.extract_attribute(
            data,
            {
                "path": "metadata.functions",
                "filter": {"visibility": "public"},
            },
        )
        assert len(result) == 1
        assert result[0]["name"] == "public_api"

    def test_nested_path_with_fallback_and_transform(self):
        """Test complex nested extraction with all Phase 2 features."""
        extractor = AdvancedAttributeExtractor()
        data = {
            "config": {
                "display": {
                    "description": "a very long description that should be truncated for display purposes"
                }
            }
        }

        result = extractor.extract_attribute(
            data,
            {
                "path": "config.display.title",
                "fallback": "config.display.description",
                "transform": {"name": "truncate", "max_length": 20},
                "default": "No description",
            },
        )
        assert len(result) <= 20
        assert result.endswith("…")

    def test_literal_value_extraction(self):
        """Test that non-string literal values are returned as-is."""
        extractor = AdvancedAttributeExtractor()
        data = {"any": "value"}

        # String paths that don't exist return None (not literal)
        result = extractor.extract_attribute(data, "missing_path")
        assert result is None

        # Non-string literals are returned as-is
        result = extractor.extract_attribute(data, 42)
        assert result == 42

        result = extractor.extract_attribute(data, True)
        assert result is True

    def test_extraction_error_handling(self):
        """Test proper error handling in complex extractions."""
        extractor = AdvancedAttributeExtractor()
        data = {"test": "value"}

        # Test malformed path expression
        with pytest.raises(ConversionError):
            extractor.extract_attribute(
                data,
                {
                    "path": "test[malformed",
                },
            )

        # Test invalid transformation
        with pytest.raises(ConversionError):
            extractor.extract_attribute(
                data, {"path": "test", "transform": "unknown_transform"}
            )
