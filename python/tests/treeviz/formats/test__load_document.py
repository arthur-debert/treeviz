"""
Unit tests for load_document function.

Tests the document loading functionality including stdin support,
format detection, and error handling.
"""

import json
import tempfile
import pytest
from io import StringIO
from unittest.mock import patch

from treeviz.formats import load_document, DocumentFormatError


class TestLoadDocument:
    """Test cases for load_document function."""

    def test_load_document_regular_file_json(self):
        """Test loading regular JSON file."""
        test_data = {"name": "test", "children": []}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(test_data, f)
            f.flush()

            result = load_document(f.name)
            assert result == test_data

    def test_load_document_regular_file_with_format_override(self):
        """Test loading file with explicit format override."""
        test_data = {"name": "test", "children": []}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".data", delete=False
        ) as f:
            json.dump(test_data, f)
            f.flush()

            result = load_document(f.name, format_name="json")
            assert result == test_data

    def test_load_document_nonexistent_file(self):
        """Test loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_document("/nonexistent/file.json")

    def test_load_document_unsupported_format(self):
        """Test loading with unsupported format raises DocumentFormatError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"test": "data"}')
            f.flush()

            with pytest.raises(
                DocumentFormatError, match="Unsupported format: invalid_format"
            ):
                load_document(f.name, format_name="invalid_format")

    @patch("sys.stdin", StringIO('{"name": "from_stdin", "type": "test"}'))
    def test_load_document_stdin_json_default(self):
        """Test loading JSON from stdin with default format."""
        result = load_document("-")
        expected = {"name": "from_stdin", "type": "test"}
        assert result == expected

    @patch("sys.stdin", StringIO('{"name": "from_stdin", "type": "test"}'))
    def test_load_document_stdin_json_explicit(self):
        """Test loading JSON from stdin with explicit JSON format."""
        result = load_document("-", format_name="json")
        expected = {"name": "from_stdin", "type": "test"}
        assert result == expected

    @patch("sys.stdin", StringIO("name: from_stdin\ntype: test\n"))
    def test_load_document_stdin_yaml_explicit(self):
        """Test loading YAML from stdin with explicit YAML format."""
        try:
            result = load_document("-", format_name="yaml")
            expected = {"name": "from_stdin", "type": "test"}
            assert result == expected
        except DocumentFormatError as e:
            # YAML might not be available, check error message
            if "Unsupported format: yaml" in str(e):
                pytest.skip("YAML format not available")
            else:
                raise

    @patch("sys.stdin", StringIO("invalid json content"))
    def test_load_document_stdin_invalid_json_default(self):
        """Test loading invalid JSON from stdin with default format gives helpful error."""
        with pytest.raises(
            DocumentFormatError,
            match="Failed to parse stdin as JSON.*--document-format",
        ):
            load_document("-")

    @patch("sys.stdin", StringIO("invalid json content"))
    def test_load_document_stdin_invalid_json_explicit(self):
        """Test loading invalid JSON from stdin with explicit format gives specific error."""
        with pytest.raises(
            DocumentFormatError, match="Failed to parse stdin as json"
        ):
            load_document("-", format_name="json")

    @patch("sys.stdin", StringIO('{"valid": "json"}'))
    def test_load_document_stdin_unsupported_format(self):
        """Test loading from stdin with unsupported format."""
        with pytest.raises(
            DocumentFormatError, match="Unsupported format: invalid_format"
        ):
            load_document("-", format_name="invalid_format")

    @patch("sys.stdin", StringIO(""))
    def test_load_document_stdin_empty_content(self):
        """Test loading empty content from stdin."""
        with pytest.raises(
            DocumentFormatError, match="Failed to parse stdin as JSON"
        ):
            load_document("-")

    @patch("sys.stdin", StringIO("{}"))
    def test_load_document_stdin_empty_json_object(self):
        """Test loading empty JSON object from stdin."""
        result = load_document("-")
        assert result == {}

    @patch("sys.stdin", StringIO("[]"))
    def test_load_document_stdin_empty_json_array(self):
        """Test loading empty JSON array from stdin."""
        result = load_document("-")
        assert result == []

    def test_load_document_delegates_to_parse_document(self):
        """Test that load_document delegates to parse_document for regular files."""
        test_data = {"name": "test", "children": []}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(test_data, f)
            f.flush()

            # This should work the same as calling parse_document directly
            result = load_document(f.name)
            assert result == test_data

    def test_load_document_preserves_parse_document_errors(self):
        """Test that load_document preserves errors from parse_document."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".unknown", delete=False
        ) as f:
            f.write("some content")
            f.flush()

            with pytest.raises(DocumentFormatError):
                load_document(f.name)


class TestLoadDocumentIntegration:
    """Integration tests for load_document with various formats."""

    def test_load_document_yaml_file(self):
        """Test loading YAML file if YAML support is available."""
        yaml_content = "name: test\nchildren: []\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                result = load_document(f.name)
                expected = {"name": "test", "children": []}
                assert result == expected
            except DocumentFormatError as e:
                if "Cannot detect format" in str(e):
                    pytest.skip("YAML format not available")
                else:
                    raise

    def test_load_document_xml_file(self):
        """Test loading XML file."""
        xml_content = '<?xml version="1.0"?><root><name>test</name></root>'

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as f:
            f.write(xml_content)
            f.flush()

            result = load_document(f.name)
            # XML parsing returns dict representation
            assert isinstance(result, dict)
            assert result["type"] == "root"
