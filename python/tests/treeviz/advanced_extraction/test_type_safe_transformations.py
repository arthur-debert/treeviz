"""
Tests for type-safe transformations in the TransformationEngine.

This test suite verifies that the second code review issue is addressed:
"Implicit Type Coercion in Transformations" - ensuring transformations
have proper type checking and provide clear error messages.
"""

import pytest
from treeviz.adapters.advanced_extraction import apply_transformation


class TestTypeSafeTextTransformations:
    """Test type safety for text transformations."""

    def test_text_transformations_with_valid_strings(self):
        """Test that text transformations work correctly with string input."""
        # Using functional API

        assert apply_transformation("hello", "upper") == "HELLO"
        assert apply_transformation("WORLD", "lower") == "world"
        assert (
            apply_transformation("hello world", "capitalize") == "Hello world"
        )
        assert apply_transformation("  spaced  ", "strip") == "spaced"

    @pytest.mark.parametrize(
        "transform_name,invalid_value",
        [
            ("upper", 123),
            ("upper", [1, 2, 3]),
            ("upper", {"key": "value"}),
            ("lower", 42),
            ("lower", True),
            ("capitalize", 3.14),
            ("strip", []),
        ],
    )
    def test_text_transformations_reject_non_string_input(
        self, transform_name, invalid_value
    ):
        """Test that text transformations raise errors for non-string input."""
        # Using functional API

        with pytest.raises(
            ValueError,
            match=f"{transform_name} transformation requires string input",
        ):
            apply_transformation(invalid_value, transform_name)


class TestTypeSafeNumericTransformations:
    """Test type safety for numeric transformations."""

    def test_numeric_transformations_with_valid_numbers(self):
        """Test that numeric transformations work correctly with numeric input."""
        # Using functional API

        assert apply_transformation(-5, "abs") == 5
        assert apply_transformation(5, "abs") == 5
        assert apply_transformation(-3.14, "abs") == 3.14

        assert (
            apply_transformation(3.14159, {"name": "round", "digits": 2})
            == 3.14
        )
        assert apply_transformation(10, {"name": "round", "digits": 0}) == 10

    @pytest.mark.parametrize(
        "transform_name,invalid_value",
        [
            ("abs", "not_a_number"),
            ("abs", [1, 2, 3]),
            ("abs", {"key": "value"}),
            ("abs", True),
            ("round", "3.14"),
            ("round", True),
            ("round", []),
        ],
    )
    def test_numeric_transformations_reject_non_numeric_input(
        self, transform_name, invalid_value
    ):
        """Test that numeric transformations raise errors for non-numeric input."""
        # Using functional API

        with pytest.raises(
            ValueError,
            match=f"{transform_name} transformation requires numeric input",
        ):
            apply_transformation(invalid_value, transform_name)


class TestTypeSafeCollectionTransformations:
    """Test type safety for collection transformations."""

    def test_collection_transformations_with_valid_collections(self):
        """Test that collection transformations work correctly with collection input."""
        # Using functional API

        # Length transformation
        assert apply_transformation([1, 2, 3], "length") == 3
        assert apply_transformation("hello", "length") == 5
        assert apply_transformation([], "length") == 0

        # Join transformation
        assert (
            apply_transformation([1, 2, 3], {"name": "join", "separator": "-"})
            == "1-2-3"
        )
        assert apply_transformation(["a", "b", "c"], "join") == "abc"

        # First and last transformations
        assert apply_transformation([1, 2, 3], "first") == 1
        assert apply_transformation([1, 2, 3], "last") == 3
        assert apply_transformation([], "first") is None
        assert apply_transformation([], "last") is None

    def test_length_transformation_rejects_invalid_input(self):
        """Test that length transformation raises errors for objects without __len__."""
        # Using functional API

        # Objects without __len__ should raise errors
        class NoLenObj:
            pass

        with pytest.raises(
            ValueError,
            match="length transformation requires object with __len__",
        ):
            apply_transformation(NoLenObj(), "length")

    def test_join_transformation_rejects_invalid_input(self):
        """Test that join transformation raises errors for non-iterable input."""
        # Using functional API

        # Non-iterables should raise errors
        class NoIterObj:
            pass

        with pytest.raises(
            ValueError, match="join transformation requires iterable"
        ):
            apply_transformation(NoIterObj(), "join")

        # Strings should be rejected (even though they're iterable)
        with pytest.raises(
            ValueError,
            match="join transformation requires iterable \\(non-string\\)",
        ):
            apply_transformation("hello", "join")

    def test_join_transformation_rejects_invalid_separator(self):
        """Test that join transformation validates separator type."""
        # Using functional API

        with pytest.raises(
            ValueError,
            match="join transformation requires string separator",
        ):
            apply_transformation([1, 2, 3], {"name": "join", "separator": 123})

    def test_first_last_transformations_reject_invalid_input(self):
        """Test that first/last transformations raise errors for invalid input."""
        # Using functional API

        # Objects without __getitem__ or __iter__ should raise errors
        class NoAccessObj:
            pass

        for transform_name in ["first", "last"]:
            with pytest.raises(
                ValueError,
                match=f"{transform_name} transformation requires",
            ):
                apply_transformation(NoAccessObj(), transform_name)


class TestTypeSafeFormatTransformation:
    """Test type safety for format transformation."""

    def test_format_transformation_with_valid_inputs(self):
        """Test that format transformation works with various input types."""
        # Using functional API

        assert (
            apply_transformation(42, {"name": "format", "format_spec": "04d"})
            == "0042"
        )
        assert (
            apply_transformation(3.14, {"name": "format", "format_spec": ".2f"})
            == "3.14"
        )
        assert (
            apply_transformation(
                "hello", {"name": "format", "format_spec": ">10"}
            )
            == "     hello"
        )

    def test_format_transformation_validates_format_spec_type(self):
        """Test that format transformation validates format_spec is a string."""
        # Using functional API

        with pytest.raises(
            ValueError,
            match="format transformation requires string format_spec",
        ):
            apply_transformation(42, {"name": "format", "format_spec": 123})

    def test_format_transformation_handles_format_errors(self):
        """Test that format transformation handles formatting errors gracefully."""
        # Using functional API

        # Invalid format spec for the value type
        with pytest.raises(ValueError, match="format transformation failed"):
            apply_transformation(
                "hello", {"name": "format", "format_spec": "04d"}
            )


class TestExplicitTypeConversions:
    """Test explicit type conversion transformations."""

    def test_explicit_str_conversion(self):
        """Test explicit string conversion."""
        # Using functional API

        assert apply_transformation(123, "str") == "123"
        assert apply_transformation(3.14, "str") == "3.14"
        assert apply_transformation(True, "str") == "True"
        assert apply_transformation([1, 2, 3], "str") == "[1, 2, 3]"
        # None values are skipped by the transformation engine for fallback chains
        assert apply_transformation(None, "str") is None

    def test_explicit_int_conversion(self):
        """Test explicit integer conversion with validation."""
        # Using functional API

        assert apply_transformation("123", "int") == 123
        assert apply_transformation(3.14, "int") == 3
        assert apply_transformation(True, "int") == 1

        # Invalid conversions should raise errors
        with pytest.raises(ValueError, match="int transformation failed"):
            apply_transformation("not_a_number", "int")

        with pytest.raises(ValueError, match="int transformation failed"):
            apply_transformation([1, 2, 3], "int")

    def test_explicit_float_conversion(self):
        """Test explicit float conversion with validation."""
        # Using functional API

        assert apply_transformation("3.14", "float") == 3.14
        assert apply_transformation(123, "float") == 123.0
        assert apply_transformation(True, "float") == 1.0

        # Invalid conversions should raise errors
        with pytest.raises(ValueError, match="float transformation failed"):
            apply_transformation("not_a_number", "float")

        with pytest.raises(ValueError, match="float transformation failed"):
            apply_transformation([1, 2, 3], "float")


class TestBackwardCompatibilityWithCustomTransformations:
    """Test that custom transformations still work without type checking."""

    def test_custom_transformation_functions_work(self):
        """Test that custom transformation functions bypass type checking."""
        # Using functional API

        def custom_transform(value):
            # Custom transformations can do their own type handling
            return f"custom: {value}"

        result = apply_transformation(123, custom_transform)
        assert result == "custom: 123"

        result = apply_transformation([1, 2, 3], custom_transform)
        assert result == "custom: [1, 2, 3]"


class TestErrorMessageQuality:
    """Test that error messages are clear and helpful."""

    def test_error_messages_include_actual_type(self):
        """Test that error messages include the actual type of the invalid input."""
        # Using functional API

        with pytest.raises(ValueError) as exc_info:
            apply_transformation(123, "upper")
        assert "got int" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            apply_transformation([1, 2, 3], "abs")
        assert "got list" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            apply_transformation("hello", "round")
        assert "got str" in str(exc_info.value)

    def test_error_messages_include_transformation_name(self):
        """Test that error messages clearly identify which transformation failed."""
        # Using functional API

        with pytest.raises(ValueError) as exc_info:
            apply_transformation(123, "upper")
        assert "upper transformation" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            apply_transformation("hello", "abs")
        assert "abs transformation" in str(exc_info.value)

    def test_error_messages_for_conversion_failures(self):
        """Test error messages for type conversion failures."""
        # Using functional API

        with pytest.raises(ValueError) as exc_info:
            apply_transformation("not_a_number", "int")
        assert "int transformation failed" in str(exc_info.value)
        assert "not_a_number" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            apply_transformation("invalid", "float")
        assert "float transformation failed" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)


class TestEdgeCasesAndSpecialValues:
    """Test edge cases and special values."""

    def test_none_values_still_skip_transformation(self):
        """Test that None values skip transformation as before."""
        # Using functional API

        # None should skip all transformations
        assert apply_transformation(None, "upper") is None
        assert apply_transformation(None, "abs") is None
        assert apply_transformation(None, "length") is None

    def test_empty_collections_work_correctly(self):
        """Test that empty collections are handled correctly."""
        # Using functional API

        assert apply_transformation([], "length") == 0
        assert apply_transformation([], "join") == ""
        assert apply_transformation([], "first") is None
        assert apply_transformation([], "last") is None

    def test_edge_cases_for_iterables(self):
        """Test edge cases with different iterable types."""
        # Using functional API

        # Tuples should work
        assert apply_transformation((1, 2, 3), "length") == 3
        assert apply_transformation((1, 2, 3), "first") == 1
        assert apply_transformation((1, 2, 3), "last") == 3

        # Sets should work for some operations
        assert apply_transformation({1, 2, 3}, "length") == 3
        # Note: first/last are undefined for sets, but shouldn't crash

        # Generators should work for iteration-based operations
        def gen():
            yield 1
            yield 2
            yield 3

        assert apply_transformation(gen(), "join") == "123"
