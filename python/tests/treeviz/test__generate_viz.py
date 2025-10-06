"""
Unit tests for generate_viz function.

Tests the main orchestration functionality with mocked sub-functions.
"""

import json
import pytest
from unittest.mock import patch

from treeviz.viz import generate_viz
from treeviz.model import Node
from tests.conftest import (
    MOCK_LOAD_DOCUMENT,
    MOCK_LOAD_ADAPTER,
    MOCK_CONVERT_DOCUMENT,
    MOCK_TEMPLATE_RENDERER,
)


class TestGenerateViz:
    """Test cases for generate_viz function."""

    @patch("sys.stdout.isatty", return_value=True)
    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    @patch(MOCK_TEMPLATE_RENDERER)
    def test_generate_viz_term_output(
        self,
        mock_clier_render,
        mock_convert,
        mock_load_adapter,
        mock_load_document,
        mock_isatty,
    ):
        """Test generate_viz with term output format."""
        # Setup mocks
        mock_document = {"name": "test", "type": "doc"}
        mock_adapter_def = {"label": "name", "type": "type"}
        mock_icons = {"doc": "📄"}
        mock_node = Node(label="test", type="doc")
        mock_rendered = "📄 test"

        # Mock clier_render
        mock_clier_render.return_value = mock_rendered

        mock_load_document.return_value = mock_document
        mock_load_adapter.return_value = (mock_adapter_def, mock_icons)
        mock_convert.return_value = mock_node

        # Call function
        result = generate_viz("test.json", output_format="term")

        # Verify calls
        mock_load_document.assert_called_once_with(
            "test.json", format_name=None
        )
        mock_load_adapter.assert_called_once_with("3viz", adapter_format=None)
        mock_convert.assert_called_once_with(mock_document, mock_adapter_def)

        # Verify clier_render was called
        mock_clier_render.assert_called_once()

        # Check the keyword arguments
        kwargs = mock_clier_render.call_args.kwargs
        assert kwargs["data"] == mock_node
        assert kwargs["format"] == "term"
        assert kwargs["template"] == "tree.j2"

        # Check context
        context = kwargs["context"]
        assert context["root_node"] == mock_node
        assert context["use_color"] is True  # stdout.isatty() is True
        assert "column_widths" in context
        assert "symbols" in context

        # Check template_dirs
        assert "template_dirs" in kwargs

        assert result == mock_rendered

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_json_output(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test generate_viz with JSON output format."""
        # Setup mocks
        mock_document = {"name": "test"}
        mock_adapter_def = {"label": "name"}
        mock_icons = {}
        mock_node = Node(label="test", type="function", content_lines=5)

        mock_load_document.return_value = mock_document
        mock_load_adapter.return_value = (mock_adapter_def, mock_icons)
        mock_convert.return_value = mock_node

        # Call function
        result = generate_viz("test.json", output_format="json")

        # Verify result is valid JSON
        parsed = json.loads(result)
        assert parsed["label"] == "test"
        assert parsed["type"] == "function"
        assert parsed["content_lines"] == 5
        assert parsed["children"] == []

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_yaml_output(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test generate_viz with YAML output format."""
        # Setup mocks
        mock_document = {"name": "test"}
        mock_adapter_def = {"label": "name"}
        mock_icons = {}
        mock_node = Node(label="test", type="simple")

        mock_load_document.return_value = mock_document
        mock_load_adapter.return_value = (mock_adapter_def, mock_icons)
        mock_convert.return_value = mock_node

        # Call function
        result = generate_viz("test.yaml", output_format="yaml")

        # Should contain YAML-like content
        assert "label: test" in result
        assert "type: simple" in result

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_with_all_parameters(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test generate_viz with all parameters specified."""
        # Setup mocks
        mock_load_document.return_value = {"data": "test"}
        mock_load_adapter.return_value = ({"label": "data"}, {})
        mock_convert.return_value = Node(label="test")

        # Call with all parameters
        result = generate_viz(
            document_path="/path/to/doc.data",
            adapter_spec="custom_adapter.yaml",
            document_format="json",
            adapter_format="yaml",
            output_format="json",
        )

        # Verify all parameters passed through
        mock_load_document.assert_called_once_with(
            "/path/to/doc.data", format_name="json"
        )
        mock_load_adapter.assert_called_once_with(
            "custom_adapter.yaml", adapter_format="yaml"
        )

        # Should return valid JSON
        parsed = json.loads(result)
        assert parsed["label"] == "test"

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_with_stdin(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test generate_viz with stdin input."""
        # Setup mocks
        mock_load_document.return_value = {"name": "from_stdin"}
        mock_load_adapter.return_value = ({"label": "name"}, {})
        mock_convert.return_value = Node(label="from_stdin")

        # Call with stdin
        result = generate_viz("-", output_format="json")

        # Verify stdin path passed through
        mock_load_document.assert_called_once_with("-", format_name=None)

        parsed = json.loads(result)
        assert parsed["label"] == "from_stdin"

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_with_ignored_node(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test generate_viz when convert_document returns None (ignored node)."""
        # Setup mocks - convert returns None for ignored node types
        mock_load_document.return_value = {"type": "comment"}
        mock_load_adapter.return_value = ({"ignore_types": ["comment"]}, {})
        mock_convert.return_value = None

        # Test JSON output with None node
        result = generate_viz("test.json", output_format="json")
        assert result == "null"

        # Test term output with None node
        result = generate_viz("test.json", output_format="term")
        assert result == ""

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    @patch(MOCK_TEMPLATE_RENDERER)
    @patch("sys.stdout.isatty")
    @patch("os.get_terminal_size")
    def test_generate_viz_terminal_width_detection(
        self,
        mock_term_size,
        mock_isatty,
        mock_clier_render,
        mock_convert,
        mock_load_adapter,
        mock_load_document,
    ):
        """Test terminal width detection for term output."""
        # Setup mocks
        mock_load_document.return_value = {"name": "test"}
        mock_load_adapter.return_value = ({"label": "name"}, {})
        mock_convert.return_value = Node(label="test")
        mock_clier_render.return_value = "output"

        # Test with specified terminal width
        generate_viz("test.json", output_format="term", terminal_width=120)

        # Should use provided terminal width
        context = mock_clier_render.call_args.kwargs["context"]
        assert context["root_node"] == Node(label="test")
        assert context["terminal_width"] == 120
        mock_clier_render.reset_mock()

        # Test without terminal width (should use default)
        generate_viz("test.json", output_format="term")

        # Should use default width
        context = mock_clier_render.call_args.kwargs["context"]
        assert context["root_node"] == Node(label="test")
        assert context["terminal_width"] == 80

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    @patch(MOCK_TEMPLATE_RENDERER)
    def test_generate_viz_text_vs_term_width(
        self,
        mock_clier_render,
        mock_convert,
        mock_load_adapter,
        mock_load_document,
    ):
        """Test difference between text and term output widths."""
        # Setup mocks
        mock_load_document.return_value = {"name": "test"}
        mock_load_adapter.return_value = ({"label": "name"}, {})
        mock_convert.return_value = Node(label="test")
        mock_clier_render.return_value = "output"

        # Test text output (fixed width)
        generate_viz("test.json", output_format="text")
        context = mock_clier_render.call_args.kwargs["context"]
        assert context["root_node"] == Node(label="test")
        assert context["terminal_width"] == 80

        mock_clier_render.reset_mock()

        # Test term output (should also use 80 as default when not TTY)
        with patch("sys.stdout.isatty", return_value=False):
            generate_viz("test.json", output_format="term")
            context = mock_clier_render.call_args.kwargs["context"]
            assert context["root_node"] == Node(label="test")
            assert context["terminal_width"] == 80

    @patch(MOCK_LOAD_DOCUMENT)
    def test_generate_viz_invalid_output_format(self, mock_load_document):
        """Test generate_viz with invalid output format."""
        mock_load_document.return_value = {"test": "data"}

        with pytest.raises(ValueError, match="Unknown output format: invalid"):
            generate_viz("test.json", output_format="invalid")

    @patch(MOCK_LOAD_DOCUMENT)
    def test_generate_viz_preserves_load_document_errors(
        self, mock_load_document
    ):
        """Test that generate_viz preserves errors from load_document."""
        from treeviz.formats import DocumentFormatError

        mock_load_document.side_effect = DocumentFormatError("Invalid format")

        with pytest.raises(DocumentFormatError, match="Invalid format"):
            generate_viz("invalid.doc")

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    def test_generate_viz_preserves_load_adapter_errors(
        self, mock_load_adapter, mock_load_document
    ):
        """Test that generate_viz preserves errors from load_adapter."""
        mock_load_document.return_value = {"test": "data"}
        mock_load_adapter.side_effect = ValueError("Unknown adapter")

        with pytest.raises(ValueError, match="Unknown adapter"):
            generate_viz("test.json", adapter_spec="unknown")

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_preserves_convert_errors(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test that generate_viz preserves errors from convert_document."""
        mock_load_document.return_value = {"test": "data"}
        mock_load_adapter.return_value = ({"invalid": "def"}, {})
        mock_convert.side_effect = KeyError("Missing field")

        with pytest.raises(KeyError, match="Missing field"):
            generate_viz("test.json")

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_with_custom_icons(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test that generate_viz passes custom icons to renderer."""
        # Setup mocks with custom icons
        mock_load_document.return_value = {"name": "test"}
        custom_icons = {"function": "⚡", "class": "🏛️", "variable": "📦"}
        mock_load_adapter.return_value = ({"label": "name"}, custom_icons)
        mock_convert.return_value = Node(label="test", type="function")

        with patch(MOCK_TEMPLATE_RENDERER) as mock_clier_render:
            mock_clier_render.return_value = "⚡ test"

            generate_viz("test.json", output_format="term")

            # Should pass custom icons to renderer
            context = mock_clier_render.call_args.kwargs["context"]
            assert context["root_node"] == Node(label="test", type="function")
            assert context["terminal_width"] == 80

    @patch(MOCK_LOAD_DOCUMENT)
    @patch(MOCK_LOAD_ADAPTER)
    @patch(MOCK_CONVERT_DOCUMENT)
    def test_generate_viz_yaml_output_normal(
        self, mock_convert, mock_load_adapter, mock_load_document
    ):
        """Test that YAML output works normally when available."""
        # Setup mocks
        mock_load_document.return_value = {"name": "test"}
        mock_load_adapter.return_value = ({"label": "name"}, {})
        mock_convert.return_value = Node(label="test", type="simple")

        result = generate_viz("test.json", output_format="yaml")

        # Should produce YAML-like output
        assert "label: test" in result
        assert "type: simple" in result
        assert "children: []" in result


class TestGenerateVizIntegration:
    """Integration tests for generate_viz with minimal mocking."""

    @patch(MOCK_LOAD_DOCUMENT)
    def test_generate_viz_with_builtin_adapter(self, mock_load_document):
        """Test generate_viz with built-in 3viz adapter (minimal mocking)."""
        # Mock document loading only
        mock_document = {
            "label": "Root Node",
            "type": "document",
            "children": [
                {"label": "Child 1", "type": "paragraph"},
                {"label": "Child 2", "type": "heading"},
            ],
        }
        mock_load_document.return_value = mock_document

        # Use real adapter pipeline
        result = generate_viz(
            "test.json", adapter_spec="3viz", output_format="json"
        )

        # Should produce valid JSON with converted structure
        parsed = json.loads(result)
        assert parsed["label"] == "Root Node"
        assert parsed["type"] == "document"
        assert len(parsed["children"]) == 2
        assert parsed["children"][0]["label"] == "Child 1"

    @patch(MOCK_LOAD_DOCUMENT)
    def test_generate_viz_with_mdast_adapter(self, mock_load_document):
        """Test generate_viz with built-in mdast adapter."""
        # MDAST-like document structure
        mdast_doc = {
            "type": "root",
            "children": [
                {
                    "type": "paragraph",
                    "children": [{"type": "text", "value": "Hello world"}],
                },
                {
                    "type": "heading",
                    "depth": 1,
                    "children": [{"type": "text", "value": "Title"}],
                },
            ],
        }
        mock_load_document.return_value = mdast_doc

        # Use real mdast adapter
        result = generate_viz(
            "test.md", adapter_spec="mdast", output_format="json"
        )

        # Should use mdast field mappings
        parsed = json.loads(result)
        assert parsed["type"] == "root"
        assert len(parsed["children"]) == 2

        # Check paragraph structure
        paragraph = parsed["children"][0]
        assert paragraph["type"] == "paragraph"
        assert len(paragraph["children"]) == 1
        assert paragraph["children"][0]["label"] == "Hello world"
