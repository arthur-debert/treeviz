"""
Tests for improved string-to-literal conversion behavior.

This module tests the enhanced extract_attribute function that provides
better feedback when path expressions fail but contain path-like characters.
"""

import logging
from treeviz.adapters.extraction.engine import extract_attribute


class TestStringLiteralFallback:
    """Test improved string-to-literal conversion behavior."""

    def test_simple_literal_string_debug_message(self, caplog):
        """Test that simple strings without path characters log debug message."""
        source_node = {"name": "test"}

        with caplog.at_level(logging.DEBUG):
            result = extract_attribute(source_node, "simple_literal")

        assert result == "simple_literal"
        assert (
            "Treating 'simple_literal' as literal value (not a valid path)"
            in caplog.text
        )
        assert "path-like characters" not in caplog.text

    def test_path_like_string_warning_message(self, caplog):
        """Test that strings with path characters but invalid syntax log warning."""
        source_node = {"c": ["item1", "item2"]}

        with caplog.at_level(logging.WARNING):
            # This has a typo: parenthesis instead of bracket
            result = extract_attribute(source_node, "c[2).invalid")

        assert result == "c[2).invalid"  # Treated as literal
        assert (
            "failed to parse but contains path-like characters" in caplog.text
        )
        assert "might be a typo" in caplog.text

    def test_various_path_like_characters_trigger_warning(self, caplog):
        """Test that different path-like characters trigger the warning."""
        source_node = {"data": "test"}

        test_cases = [
            (
                "field.invalid",
                "valid but returned None",
            ),  # Valid path, missing field
            ("field[invalid", "failed to parse"),  # Syntax error
            ("field]invalid", "failed to parse"),  # Syntax error
            (
                "field[0.invalid]",
                "failed to parse",
            ),  # Syntax error (dots not allowed in brackets)
        ]

        for invalid_path, expected_message_fragment in test_cases:
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                result = extract_attribute(source_node, invalid_path)

            assert result == invalid_path  # Treated as literal
            assert (
                expected_message_fragment in caplog.text
            ), f"Failed for: {invalid_path}, got: {caplog.text}"

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

    def test_pure_literals_work_without_warning(self, caplog):
        """Test that strings clearly intended as literals don't trigger warnings."""
        source_node = {"data": "test"}

        literal_strings = [
            "Plain Text",
            "123",
            "hello world",
            "Title: Something",
            "value_without_dots_or_brackets",
        ]

        for literal in literal_strings:
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                result = extract_attribute(source_node, literal)

            assert result == literal
            # Should have debug message but not warning
            assert (
                "Treating" in caplog.text and "as literal value" in caplog.text
            )
            assert "path-like characters" not in caplog.text
            assert "might be a typo" not in caplog.text
