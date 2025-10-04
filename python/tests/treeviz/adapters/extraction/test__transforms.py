"""
Unit tests for transformation functions.

Tests each transformation function in isolation for edge cases and type safety.
"""

import pytest
from unittest.mock import Mock

from treeviz.adapters.extraction.transforms import (
    apply_transformation,
    _apply_builtin_transformation,
    _truncate_text,
    _text_upper,
    _text_lower,
    _text_capitalize,
    _text_strip,
    _numeric_abs,
    _numeric_round,
    _format_value,
    _collection_length,
    _collection_join,
    _collection_first,
    _collection_last,
    _convert_to_str,
    _convert_to_int,
    _convert_to_float,
)


class TestApplyTransformation:
    """Test the main apply_transformation function."""

    def test_none_value_passthrough(self):
        """Test that None values are passed through unchanged."""
        assert apply_transformation(None, "upper") is None
        assert (
            apply_transformation(None, {"name": "truncate", "max_length": 5})
            is None
        )
        assert apply_transformation(None, lambda x: x.upper()) is None

    def test_callable_transformation(self):
        """Test custom callable transformations."""
        def custom_func(x):
            return f"custom_{x}"
        result = apply_transformation("test", custom_func)
        assert result == "custom_test"

    def test_string_transformation_spec(self):
        """Test simple string transformation specifications."""
        result = apply_transformation("hello", "upper")
        assert result == "HELLO"

    def test_dict_transformation_spec(self):
        """Test dict transformation specifications with parameters."""
        result = apply_transformation(
            "hello world", {"name": "truncate", "max_length": 5}
        )
        assert result == "hell…"

    def test_dict_transformation_missing_name(self):
        """Test dict transformation without name field raises error."""
        with pytest.raises(ValueError, match="must include 'name' field"):
            apply_transformation("test", {"max_length": 5})

    def test_invalid_transformation_spec_type(self):
        """Test invalid transformation spec type raises error."""
        with pytest.raises(
            ValueError, match="Invalid transformation specification type"
        ):
            apply_transformation("test", 123)

    def test_transformation_failure_wrapped(self):
        """Test that non-ValueError exceptions are wrapped."""

        def failing_transform(x):
            raise RuntimeError("Something went wrong")

        with pytest.raises(
            ValueError, match="Transformation failed: Something went wrong"
        ):
            apply_transformation("test", failing_transform)

    def test_value_error_passthrough(self):
        """Test that ValueError exceptions are passed through unchanged."""

        def failing_transform(x):
            raise ValueError("Original error")

        with pytest.raises(ValueError, match="Original error"):
            apply_transformation("test", failing_transform)


class TestBuiltinTransformations:
    """Test built-in transformation functions."""

    def test_unknown_transformation(self):
        """Test unknown transformation name raises error with available list."""
        with pytest.raises(ValueError) as exc_info:
            _apply_builtin_transformation("test", "unknown")

        error_msg = str(exc_info.value)
        assert "Unknown transformation 'unknown'" in error_msg
        assert "Available:" in error_msg
        assert "upper" in error_msg  # Should list available transformations


class TestTruncateText:
    """Test _truncate_text function for edge cases."""

    def test_truncate_text_edge_cases(self):
        """Test edge cases for text truncation."""
        # Max length zero
        assert _truncate_text("hello", max_length=0) == ""

        # Max length less than suffix length
        assert _truncate_text("hello", max_length=1, suffix="...") == "."

        # Suffix longer than max_length
        assert _truncate_text("hello", max_length=2, suffix="...") == ".."

        # Custom suffix
        assert (
            _truncate_text("hello world", max_length=7, suffix=">>")
            == "hello>>"
        )


class TestTextTransformationErrors:
    """Test type safety for text transformations."""

    def test_upper_non_string_error(self):
        """Test upper transformation with non-string input."""
        with pytest.raises(
            ValueError,
            match="upper transformation requires string input, got int",
        ):
            _text_upper(123)

    def test_lower_non_string_error(self):
        """Test lower transformation with non-string input."""
        with pytest.raises(
            ValueError,
            match="lower transformation requires string input, got list",
        ):
            _text_lower([1, 2, 3])

    def test_capitalize_non_string_error(self):
        """Test capitalize transformation with non-string input."""
        with pytest.raises(
            ValueError,
            match="capitalize transformation requires string input, got float",
        ):
            _text_capitalize(3.14)

    def test_strip_non_string_error(self):
        """Test strip transformation with non-string input."""
        with pytest.raises(
            ValueError,
            match="strip transformation requires string input, got dict",
        ):
            _text_strip({"key": "value"})


class TestNumericTransformationErrors:
    """Test type safety for numeric transformations."""

    def test_abs_non_numeric_error(self):
        """Test abs transformation with non-numeric input."""
        with pytest.raises(
            ValueError,
            match="abs transformation requires numeric input, got str",
        ):
            _numeric_abs("hello")

    def test_abs_boolean_error(self):
        """Test abs transformation rejects boolean input."""
        with pytest.raises(
            ValueError,
            match="abs transformation requires numeric input, got bool",
        ):
            _numeric_abs(True)

    def test_round_non_numeric_error(self):
        """Test round transformation with non-numeric input."""
        with pytest.raises(
            ValueError,
            match="round transformation requires numeric input, got list",
        ):
            _numeric_round([1, 2, 3])

    def test_round_boolean_error(self):
        """Test round transformation rejects boolean input."""
        with pytest.raises(
            ValueError,
            match="round transformation requires numeric input, got bool",
        ):
            _numeric_round(False)


class TestFormatValueErrors:
    """Test format_value function error cases."""

    def test_format_non_string_spec_error(self):
        """Test format transformation with non-string format spec."""
        with pytest.raises(
            ValueError,
            match="format transformation requires string format_spec, got int",
        ):
            _format_value(123, 456)

    def test_format_invalid_spec_error(self):
        """Test format transformation with invalid format spec."""
        with pytest.raises(
            ValueError, match="format transformation failed.*invalid"
        ):
            _format_value("hello", "{invalid}")


class TestCollectionTransformationErrors:
    """Test type safety for collection transformations."""

    def test_length_no_len_error(self):
        """Test length transformation with object without __len__."""

        class NoLen:
            pass

        with pytest.raises(
            ValueError,
            match="length transformation requires object with __len__, got NoLen",
        ):
            _collection_length(NoLen())

    def test_length_type_error(self):
        """Test length transformation TypeError handling."""
        # Mock object that has __len__ but raises TypeError
        mock_obj = Mock()
        mock_obj.__len__ = Mock(side_effect=TypeError("len failed"))

        with pytest.raises(
            ValueError, match="length transformation failed.*len failed"
        ):
            _collection_length(mock_obj)

    def test_join_string_input_error(self):
        """Test join transformation rejects string input."""
        with pytest.raises(
            ValueError,
            match="join transformation requires iterable \\(non-string\\), got str",
        ):
            _collection_join("hello")

    def test_join_bytes_input_error(self):
        """Test join transformation rejects bytes input."""
        with pytest.raises(
            ValueError,
            match="join transformation requires iterable \\(non-string\\), got bytes",
        ):
            _collection_join(b"hello")

    def test_join_non_string_separator_error(self):
        """Test join transformation with non-string separator."""
        with pytest.raises(
            ValueError,
            match="join transformation requires string separator, got int",
        ):
            _collection_join([1, 2, 3], 123)

    def test_join_type_error(self):
        """Test join transformation TypeError handling."""
        # Mock object that's iterable but causes join to fail
        mock_obj = Mock()
        mock_obj.__iter__ = Mock(
            return_value=iter([Mock()])
        )  # Mock objects that will fail str()

        # Mock the str() method to raise TypeError
        mock_item = Mock()
        mock_item.__str__ = Mock(side_effect=TypeError("str conversion failed"))
        mock_obj.__iter__ = Mock(return_value=iter([mock_item]))

        with pytest.raises(ValueError, match="join transformation failed"):
            _collection_join(mock_obj)


class TestCollectionFirstLastErrors:
    """Test error cases for first/last transformations."""

    def test_first_invalid_input_error(self):
        """Test first transformation with invalid input."""

        class NoAccess:
            pass

        with pytest.raises(
            ValueError,
            match="first transformation requires indexable or iterable, got NoAccess",
        ):
            _collection_first(NoAccess())

    def test_first_index_error(self):
        """Test first transformation IndexError handling."""
        # Mock object that has __getitem__ but raises IndexError
        mock_obj = Mock()
        mock_obj.__getitem__ = Mock(
            side_effect=IndexError("index out of range")
        )
        mock_obj.__len__ = Mock(
            return_value=1
        )  # Non-zero length to trigger indexing

        with pytest.raises(
            ValueError, match="first transformation failed.*index out of range"
        ):
            _collection_first(mock_obj)

    def test_first_type_error(self):
        """Test first transformation TypeError handling."""

        # Create a proper mock with __getitem__ that triggers the len() call path
        class MockWithGetItem:
            def __getitem__(self, key):
                return f"item_{key}"

            def __len__(self):
                raise TypeError("len failed")

        with pytest.raises(
            ValueError, match="first transformation failed.*len failed"
        ):
            _collection_first(MockWithGetItem())

    def test_last_invalid_input_error(self):
        """Test last transformation with invalid input."""

        class NoAccess:
            pass

        with pytest.raises(
            ValueError,
            match="last transformation requires indexable or iterable, got NoAccess",
        ):
            _collection_last(NoAccess())

    def test_last_index_error(self):
        """Test last transformation IndexError handling."""
        # Mock object that has __getitem__ but raises IndexError
        mock_obj = Mock()
        mock_obj.__getitem__ = Mock(
            side_effect=IndexError("index out of range")
        )
        mock_obj.__len__ = Mock(
            return_value=1
        )  # Non-zero length to trigger indexing

        with pytest.raises(
            ValueError, match="last transformation failed.*index out of range"
        ):
            _collection_last(mock_obj)

    def test_last_type_error(self):
        """Test last transformation TypeError handling."""

        # Create a proper mock with __getitem__ that triggers the len() call path
        class MockWithGetItem:
            def __getitem__(self, key):
                return f"item_{key}"

            def __len__(self):
                raise TypeError("len failed")

        with pytest.raises(
            ValueError, match="last transformation failed.*len failed"
        ):
            _collection_last(MockWithGetItem())


class TestTypeConversionErrors:
    """Test error cases for type conversion transformations."""

    def test_str_conversion_error(self):
        """Test str conversion error handling."""
        # Mock object that raises error during str conversion
        mock_obj = Mock()
        mock_obj.__str__ = Mock(side_effect=RuntimeError("str failed"))

        with pytest.raises(
            ValueError, match="str transformation failed.*str failed"
        ):
            _convert_to_str(mock_obj)

    def test_int_conversion_error(self):
        """Test int conversion error handling."""
        with pytest.raises(
            ValueError, match="int transformation failed.*invalid literal"
        ):
            _convert_to_int("not_a_number")

    def test_float_conversion_error(self):
        """Test float conversion error handling."""
        with pytest.raises(
            ValueError, match="float transformation failed.*could not convert"
        ):
            _convert_to_float("not_a_float")


class TestIteratorFallback:
    """Test iterator fallback behavior for first/last transformations."""

    def test_first_iterator_fallback(self):
        """Test first transformation falls back to iterator when no __getitem__."""

        class IterableOnly:
            def __iter__(self):
                return iter([10, 20, 30])

        result = _collection_first(IterableOnly())
        assert result == 10

    def test_first_iterator_empty(self):
        """Test first transformation with empty iterator."""

        class EmptyIterable:
            def __iter__(self):
                return iter([])

        result = _collection_first(EmptyIterable())
        assert result is None

    def test_last_iterator_fallback(self):
        """Test last transformation falls back to iterator when no __getitem__."""

        class IterableOnly:
            def __iter__(self):
                return iter([10, 20, 30])

        result = _collection_last(IterableOnly())
        assert result == 30

    def test_last_iterator_empty(self):
        """Test last transformation with empty iterator."""

        class EmptyIterable:
            def __iter__(self):
                return iter([])

        result = _collection_last(EmptyIterable())
        assert result is None
