"""
Tests for the robust path expression parser.

This test suite verifies that the new PathParser is more robust and maintainable
than the previous regex-based approach, addressing the code review feedback.
"""

import pytest
from treeviz.adapters.extraction import (
    parse_path_expression,
)


class TestRobustPathParser:
    """Test the robust recursive descent path parser."""

    def test_simple_attributes(self):
        """Test simple attribute access."""
        result = parse_path_expression("name")
        assert result == [{"type": "attribute", "name": "name"}]

        result = parse_path_expression("_private")
        assert result == [{"type": "attribute", "name": "_private"}]

        result = parse_path_expression("var123")
        assert result == [{"type": "attribute", "name": "var123"}]

    def test_dot_notation(self):
        """Test dot notation for nested access."""
        result = parse_path_expression("def_.database.host")
        expected = [
            {"type": "attribute", "name": "def_"},
            {"type": "attribute", "name": "database"},
            {"type": "attribute", "name": "host"},
        ]
        assert result == expected

    def test_array_access(self):
        """Test array indexing with positive and negative indices."""

        # Positive index
        result = parse_path_expression("items[0]")
        expected = [
            {"type": "attribute", "name": "items"},
            {"type": "index", "index": 0},
        ]
        assert result == expected

        # Negative index
        result = parse_path_expression("items[-1]")
        expected = [
            {"type": "attribute", "name": "items"},
            {"type": "index", "index": -1},
        ]
        assert result == expected

    def test_string_keys(self):
        """Test string key access with quoted strings."""

        # Double quoted
        result = parse_path_expression('data["complex-key"]')
        expected = [
            {"type": "attribute", "name": "data"},
            {"type": "key", "key": "complex-key"},
        ]
        assert result == expected

        # Single quoted
        result = parse_path_expression("data['key']")
        expected = [
            {"type": "attribute", "name": "data"},
            {"type": "key", "key": "key"},
        ]
        assert result == expected

        # Unquoted (backward compatibility)
        result = parse_path_expression("data[key]")
        expected = [
            {"type": "attribute", "name": "data"},
            {"type": "key", "key": "key"},
        ]
        assert result == expected

    def test_consecutive_brackets(self):
        """Test consecutive bracket notation like matrix[0][1]."""
        result = parse_path_expression("matrix[0][1]")
        expected = [
            {"type": "attribute", "name": "matrix"},
            {"type": "index", "index": 0},
            {"type": "index", "index": 1},
        ]
        assert result == expected

        result = parse_path_expression('data["key1"]["key2"]')
        expected = [
            {"type": "attribute", "name": "data"},
            {"type": "key", "key": "key1"},
            {"type": "key", "key": "key2"},
        ]
        assert result == expected

    def test_complex_expressions(self):
        """Test complex nested expressions."""
        result = parse_path_expression('users[0].settings["theme"].colors[1]')
        expected = [
            {"type": "attribute", "name": "users"},
            {"type": "index", "index": 0},
            {"type": "attribute", "name": "settings"},
            {"type": "key", "key": "theme"},
            {"type": "attribute", "name": "colors"},
            {"type": "index", "index": 1},
        ]
        assert result == expected

    def test_bracket_only_expressions(self):
        """Test expressions that start with brackets."""
        result = parse_path_expression("[0]")
        assert result == [{"type": "index", "index": 0}]

        result = parse_path_expression('["key"]')
        assert result == [{"type": "key", "key": "key"}]

    def test_whitespace_handling(self):
        """Test that whitespace in brackets is handled correctly."""
        result = parse_path_expression("items[ 0 ]")
        expected = [
            {"type": "attribute", "name": "items"},
            {"type": "index", "index": 0},
        ]
        assert result == expected

        result = parse_path_expression('data[ "key" ]')
        expected = [
            {"type": "attribute", "name": "data"},
            {"type": "key", "key": "key"},
        ]
        assert result == expected

    def test_error_cases(self):
        """Test various error conditions with clear error messages."""
        # Empty path
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_path_expression("")

        # Unclosed bracket
        with pytest.raises(ValueError, match="Unclosed bracket"):
            parse_path_expression("items[0")

        # Invalid character in identifier position
        with pytest.raises(ValueError, match="Expected identifier"):
            parse_path_expression("123invalid")

        # Empty bracket
        with pytest.raises(ValueError, match="Empty key"):
            parse_path_expression("items[]")

        # Unclosed string
        with pytest.raises(ValueError, match="Unclosed string"):
            parse_path_expression('items["unclosed')

        # Invalid number
        with pytest.raises(ValueError, match="Expected digit"):
            parse_path_expression("items[-]")

        # Unexpected character
        with pytest.raises(ValueError, match="Unexpected character"):
            parse_path_expression("items[0]@")

    def test_edge_cases(self):
        """Test edge cases that were problematic with the old parser."""

        # Large numbers
        result = parse_path_expression("items[999999]")
        assert result[1]["index"] == 999999

        # Empty string key
        result = parse_path_expression('data[""]')
        assert result[1]["key"] == ""

        # Special characters in quoted strings
        result = parse_path_expression(
            'data["key-with-dashes_and_underscores"]'
        )
        assert result[1]["key"] == "key-with-dashes_and_underscores"

        # Mixed access patterns
        result = parse_path_expression('root["def_"].items[0].nested["key"]')
        expected = [
            {"type": "attribute", "name": "root"},
            {"type": "key", "key": "def_"},
            {"type": "attribute", "name": "items"},
            {"type": "index", "index": 0},
            {"type": "attribute", "name": "nested"},
            {"type": "key", "key": "key"},
        ]
        assert result == expected


class TestPathParserRobustness:
    """Test that the new parser is more robust than the old approach."""

    def test_maintainability(self):
        """Test that complex expressions are handled cleanly."""

        # These expressions caused issues with the old regex-based parser
        test_cases = [
            'a.b[0].c["d"][1].e',
            "matrix[0][1][2]",
            'def_["database"]["host"]',
            "users[-1].permissions[0]",
            'deeply.nested[0]["complex-key"].items[-1].value',
        ]

        for test_case in test_cases:
            # Should not raise any errors
            result = parse_path_expression(test_case)
            assert len(result) > 0
            # All steps should have proper types
            for step in result:
                assert step["type"] in ["attribute", "index", "key"]

    def test_clear_error_messages(self):
        """Test that error messages are clear and include position information."""

        # Test specific error positions
        with pytest.raises(ValueError) as exc_info:
            parse_path_expression("items[0@")
        assert "position 7" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            parse_path_expression("items[")
        assert "Unclosed bracket" in str(exc_info.value)

    def test_parser_consistency(self):
        """Test that parsing is consistent and deterministic."""

        test_case = 'complex.path[0]["key"].nested[-1]'

        # Parse multiple times - should be identical
        result1 = parse_path_expression(test_case)
        result2 = parse_path_expression(test_case)
        result3 = parse_path_expression(test_case)

        assert result1 == result2 == result3
