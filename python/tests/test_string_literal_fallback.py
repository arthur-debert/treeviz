"""
Tests for improved string-to-literal conversion behavior.

This module tests the enhanced extract_attribute function that provides
better feedback when path expressions fail but contain path-like characters.
"""

import logging
from treeviz.adapters.extraction.engine import extract_attribute


class TestStringLiteralFallback:
    """Test string path extraction and literal fallback behavior."""

    def test_simple_field_name_returns_none_when_missing(self, caplog):
        """Test that simple field names return None when the field doesn't exist."""
        source_node = {"name": "test"}

        with caplog.at_level(logging.DEBUG):
            result = extract_attribute(source_node, "missing_field")

        assert result is None
        # Should not log anything special - this is normal behavior

    def test_invalid_path_syntax_treated_as_literal(self, caplog):
        """Test that strings with invalid path syntax are treated as literals."""
        source_node = {"c": ["item1", "item2"]}

        with caplog.at_level(logging.DEBUG):
            # This has a typo: parenthesis instead of bracket
            result = extract_attribute(source_node, "c[2).invalid")

        assert result == "c[2).invalid"  # Treated as literal
        assert "failed to parse, treating as literal" in caplog.text

    def test_various_invalid_paths_behavior(self, caplog):
        """Test behavior of various invalid path expressions."""
        source_node = {"data": "test"}

        test_cases = [
            ("field.invalid", None),  # Valid path syntax, missing field -> None
            ("field[invalid", "field[invalid"),  # Syntax error -> literal
            ("field]invalid", "field]invalid"),  # Syntax error -> literal
            ("field[0.invalid]", "field[0.invalid]"),  # Syntax error -> literal
        ]

        for invalid_path, expected_result in test_cases:
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                result = extract_attribute(source_node, invalid_path)

            assert result == expected_result, f"Failed for: {invalid_path}"

    def test_valid_paths_dont_trigger_fallback(self):
        """Test that valid paths work normally without fallback."""
        source_node = {
            "simple": "value",
            "nested": {"field": "nested_value"},
            "array": ["item0", "item1"],
        }

        test_cases = [
            ("simple", "value"),
            ("nested.field", "nested_value"),
            ("array[0]", "item0"),
            ("array[1]", "item1"),
        ]

        for path, expected in test_cases:
            result = extract_attribute(source_node, path)
            assert result == expected

    def test_literal_values_via_parse_failure(self, caplog):
        """Test that strings that fail parsing are treated as literals."""
        source_node = {"data": "test"}

        literal_strings = [
            "Plain Text",  # Space makes it unparseable
            "hello world",  # Space makes it unparseable
            "Title: Something",  # Colon makes it unparseable
        ]

        for literal in literal_strings:
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                result = extract_attribute(source_node, literal)

            assert result == literal
            assert "failed to parse, treating as literal" in caplog.text

        # Test that simple identifiers that could be field names return None
        simple_identifiers = [
            "value_without_dots_or_brackets",
            "field_name",
            "test123",
        ]
        for identifier in simple_identifiers:
            caplog.clear()
            result = extract_attribute(source_node, identifier)
            assert result is None  # Field doesn't exist, so None
