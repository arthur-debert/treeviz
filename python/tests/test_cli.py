"""
Tests for the 3viz CLI functionality.
"""

import json
import pytest
from click.testing import CliRunner

from treeviz.cli import cli


class TestCLIStructure:
    """Test basic CLI structure and commands."""

    def test_cli_help(self):
        """Test main CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "3viz AST visualization tool" in result.output
        assert "get-definition" in result.output

    def test_format_option_help(self):
        """Test that format option appears in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--format [text|json|term]" in result.output

    def test_get_definition_help(self):
        """Test get-definition command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-definition", "--help"])
        assert result.exit_code == 0
        assert "Get a definition for the specified format" in result.output


class TestGetDefinitionCommand:
    """Test the get-definition command functionality."""

    def test_get_definition_3viz_default(self):
        """Test getting 3viz definition (default)."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-definition"])
        assert result.exit_code == 0

        # Should output valid JSON
        output_data = json.loads(result.output)
        assert "label" in output_data
        assert "icons" in output_data
        assert output_data["label"] == "label"  # Definition.default() uses "label"

    def test_get_definition_3viz_explicit(self):
        """Test getting 3viz definition explicitly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-definition", "3viz"])
        assert result.exit_code == 0

        output_data = json.loads(result.output)
        assert output_data["label"] == "label"  # Definition.default() uses "label"
        assert output_data["type"] == "type"    # Definition.default() uses "type"
        assert output_data["children"] == "children"

    def test_get_definition_mdast(self):
        """Test getting mdast definition."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-definition", "mdast"])
        assert result.exit_code == 0

        output_data = json.loads(result.output)
        assert "label" in output_data
        assert "icons" in output_data

    def test_get_definition_unknown_format(self):
        """Test error handling for unknown format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-definition", "unknown"])
        # This should fail because 'unknown' is not in the valid choices
        assert result.exit_code != 0


class TestFormatOptions:
    """Test output format options."""

    def test_format_json_explicit(self):
        """Test explicit JSON format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--format", "json", "get-definition", "3viz"]
        )
        assert result.exit_code == 0

        # Should be valid JSON
        output_data = json.loads(result.output)
        assert "label" in output_data

    def test_format_text_explicit(self):
        """Test explicit text format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--format", "text", "get-definition", "3viz"]
        )
        assert result.exit_code == 0

        # For now, text format outputs JSON (as per requirements)
        output_data = json.loads(result.output)
        assert "label" in output_data

    def test_format_term_explicit(self):
        """Test explicit term format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--format", "term", "get-definition", "3viz"]
        )
        assert result.exit_code == 0

        # For now, term format outputs JSON (as per requirements)
        output_data = json.loads(result.output)
        assert "label" in output_data


class TestErrorHandling:
    """Test error handling in CLI commands."""

    def test_invalid_format_option(self):
        """Test invalid format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--format", "invalid", "get-definition"])
        assert result.exit_code != 0
        assert "Invalid value for '--format'" in result.output


class TestMainModule:
    """Test the __main__ module entry point."""

    def test_main_module_import(self):
        """Test that __main__ module can be imported."""

        # Should not raise any exceptions


class TestOutputHelper:
    """Test internal output helper functions."""

    def test_output_data_json(self):
        """Test _output_data function with JSON format."""
        from treeviz.__main__ import _output_data
        from io import StringIO
        import sys

        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output

        test_data = {"test": "value"}
        _output_data(test_data, "json")

        # Reset stdout
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        assert json.loads(output) == test_data

    def test_output_data_text(self):
        """Test _output_data function with text format."""
        from treeviz.__main__ import _output_data
        from io import StringIO
        import sys

        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output

        test_data = {"test": "value"}
        _output_data(test_data, "text")

        # Reset stdout
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        # Text format should also output JSON for now
        assert json.loads(output) == test_data

    def test_output_data_invalid_format(self):
        """Test _output_data function with invalid format."""
        from treeviz.__main__ import _output_data

        with pytest.raises(ValueError, match="Unknown output format"):
            _output_data({}, "invalid")
