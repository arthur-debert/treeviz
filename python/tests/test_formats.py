"""
Test document format parsing functionality.

This module tests the Format dataclass, format registry, and parse_document
function with various input formats.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from treeviz.formats import (
    Format,
    DocumentFormatError,
    parse_document,
    register_format,
    get_supported_formats,
)
from treeviz.formats.parser import detect_format, get_format_by_name, _FORMATS


def get_test_data_path(filename: str) -> str:
    """Get path to test data file."""
    return str(
        Path(__file__).parent.parent.parent / "test-data" / "formats" / filename
    )


class TestFormat:
    """Test Format dataclass functionality."""

    def test_format_creation(self):
        """Test basic Format creation."""

        def dummy_parser(content):
            return {"parsed": content}

        format_obj = Format(
            name="Test",
            extensions=[".test", ".tst"],
            parse_func=dummy_parser,
            description="Test format",
        )

        assert format_obj.name == "Test"
        assert format_obj.extensions == [".test", ".tst"]
        assert format_obj.description == "Test format"

    def test_format_can_handle(self):
        """Test file path handling detection."""
        format_obj = Format(
            name="Test", extensions=[".json", ".jsonl"], parse_func=lambda x: x
        )

        assert format_obj.can_handle("test.json") is True
        assert format_obj.can_handle("test.JSON") is True  # Case insensitive
        assert format_obj.can_handle("test.jsonl") is True
        assert format_obj.can_handle("test.yaml") is False
        assert format_obj.can_handle("test.txt") is False

    def test_format_parse_success(self):
        """Test successful parsing."""

        def mock_parser(content):
            return {"content": content, "parsed": True}

        format_obj = Format(
            name="Mock", extensions=[".mock"], parse_func=mock_parser
        )

        result = format_obj.parse("test content")
        assert result == {"content": "test content", "parsed": True}

    def test_format_parse_failure(self):
        """Test parsing failure handling."""

        def failing_parser(content):
            raise ValueError("Parse error")

        format_obj = Format(
            name="Failing", extensions=[".fail"], parse_func=failing_parser
        )

        with pytest.raises(DocumentFormatError) as exc_info:
            format_obj.parse("test content")

        assert "Failed to parse content as Failing" in str(exc_info.value)
        assert "Parse error" in str(exc_info.value)


class TestFormatRegistry:
    """Test format registration and detection."""

    def setup_method(self):
        """Set up test environment."""
        # Save original formats
        self.original_formats = _FORMATS.copy()

        # Clear registry for testing
        _FORMATS.clear()

        # Register test format
        self.test_format = Format(
            name="TestFormat",
            extensions=[".test"],
            parse_func=lambda x: {"test": x},
        )
        register_format(self.test_format)

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original formats
        _FORMATS.clear()
        _FORMATS.update(self.original_formats)

    def test_register_format(self):
        """Test format registration."""
        assert "testformat" in _FORMATS
        assert _FORMATS["testformat"] == self.test_format

    def test_get_supported_formats(self):
        """Test getting supported format names."""
        formats = get_supported_formats()
        assert "testformat" in formats

    def test_get_format_by_name(self):
        """Test getting format by name."""
        format_obj = get_format_by_name("TestFormat")
        assert format_obj == self.test_format

        format_obj = get_format_by_name("testformat")  # Case insensitive
        assert format_obj == self.test_format

        format_obj = get_format_by_name("nonexistent")
        assert format_obj is None

    def test_detect_format(self):
        """Test format auto-detection."""
        format_obj = detect_format("test.test")
        assert format_obj == self.test_format

        format_obj = detect_format("test.unknown")
        assert format_obj is None


class TestParseDocument:
    """Test parse_document function."""

    def test_parse_json_file(self):
        """Test parsing JSON file."""
        # Use existing test data
        test_file = get_test_data_path("sample.json")

        result = parse_document(test_file)

        assert isinstance(result, dict)
        assert result["type"] == "document"
        assert result["title"] == "Sample Document"
        assert len(result["children"]) == 3

    def test_parse_json_with_explicit_format(self):
        """Test parsing with explicitly specified format."""
        test_file = get_test_data_path("simple.json")

        result = parse_document(test_file, format_name="json")

        assert isinstance(result, dict)
        assert result["name"] == "root"
        assert result["type"] == "element"

    def test_parse_yaml_file(self):
        """Test parsing YAML file if YAML is available."""
        test_file = get_test_data_path("sample.yaml")

        # Check if YAML format is available
        yaml_format = get_format_by_name("yaml")
        if yaml_format is None:
            pytest.skip("YAML format not available")

        result = parse_document(test_file)

        assert isinstance(result, dict)
        assert result["type"] == "document"
        assert result["title"] == "Sample Document"

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        with pytest.raises(FileNotFoundError):
            parse_document("nonexistent.json")

    def test_parse_malformed_json(self):
        """Test parsing malformed JSON."""
        test_file = get_test_data_path("malformed.json")

        with pytest.raises(DocumentFormatError) as exc_info:
            parse_document(test_file)

        assert "Failed to parse content as JSON" in str(exc_info.value)

    def test_parse_unsupported_format_name(self):
        """Test parsing with unsupported format name."""
        test_file = get_test_data_path("sample.json")

        with pytest.raises(DocumentFormatError) as exc_info:
            parse_document(test_file, format_name="unsupported")

        assert "Unsupported format: unsupported" in str(exc_info.value)

    def test_parse_unsupported_extension(self):
        """Test parsing file with unsupported extension."""
        # Create a temporary file with unsupported extension
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".unknown", delete=False
        ) as f:
            f.write('{"test": "data"}')
            temp_file = f.name

        try:
            with pytest.raises(DocumentFormatError) as exc_info:
                parse_document(temp_file)

            assert "Cannot detect format for file" in str(exc_info.value)
        finally:
            # Clean up
            Path(temp_file).unlink()

    @patch("pathlib.Path.read_text")
    def test_parse_unicode_error(self, mock_read_text):
        """Test handling of Unicode decode errors."""
        mock_read_text.side_effect = UnicodeDecodeError(
            "utf-8", b"\x80", 0, 1, "invalid start byte"
        )

        test_file = get_test_data_path("sample.json")

        with pytest.raises(DocumentFormatError) as exc_info:
            parse_document(test_file)

        assert "Failed to read file as UTF-8" in str(exc_info.value)


class TestBuiltinFormats:
    """Test built-in format implementations."""

    def test_json_format_registered(self):
        """Test that JSON format is registered by default."""
        json_format = get_format_by_name("json")
        assert json_format is not None
        assert json_format.name == "JSON"
        assert ".json" in json_format.extensions
        assert ".jsonl" in json_format.extensions

    def test_yaml_format_conditional(self):
        """Test that YAML format is conditionally registered."""
        yaml_format = get_format_by_name("yaml")

        # YAML format should be available if ruamel.yaml is installed
        try:
            import importlib.util

            yaml_spec = importlib.util.find_spec("ruamel.yaml")
            if yaml_spec is not None:
                assert yaml_format is not None
                assert yaml_format.name == "YAML"
                assert ".yaml" in yaml_format.extensions
                assert ".yml" in yaml_format.extensions
            else:
                assert yaml_format is None
        except ImportError:
            assert yaml_format is None


class TestIntegrationWithAdapters:
    """Test that format parsing integrates properly with adapters."""

    def test_parse_and_adapt_workflow(self):
        """Test the complete workflow: parse document -> adapt with adapter."""
        from treeviz.adapters.adapters import adapt_node

        # Parse document
        test_file = get_test_data_path("simple.json")
        parsed_data = parse_document(test_file)

        # Define adapter
        adapter_def = {"label": "value", "type": "type", "children": "children"}

        # Adapt the parsed data
        result = adapt_node(parsed_data, adapter_def)

        # Verify the result
        assert result.label == "Root content"
        assert result.type == "element"
        assert len(result.children) == 2
        assert result.children[0].label == "First child"
        assert result.children[1].label == "Second child"

    def test_orthogonality_principle(self):
        """Test that format parsing is orthogonal to adapter selection."""
        from treeviz.adapters.adapters import adapt_node

        # Step 1: Parse documents from different formats into pure Python
        json_data = parse_document(get_test_data_path("sample.json"))

        yaml_format = get_format_by_name("yaml")
        if yaml_format:
            yaml_data = parse_document(get_test_data_path("sample.yaml"))

            # Both should produce identical pure Python objects
            assert json_data == yaml_data
            assert isinstance(json_data, dict) and isinstance(yaml_data, dict)

            # Step 2: Apply the SAME adapter to both parsed results
            # (This demonstrates orthogonality - format parsing is done, now it's just Python)
            adapter_def = {
                "label": "title",
                "type": "type",
                "children": "children",
            }

            json_result = adapt_node(json_data, adapter_def)
            yaml_result = adapt_node(yaml_data, adapter_def)

            # Results should be identical since the underlying data is identical
            assert json_result.label == yaml_result.label
            assert json_result.type == yaml_result.type
            assert len(json_result.children) == len(yaml_result.children)
