"""
Unit tests for formats/parser.py

Tests format registry, detection, and parsing functionality including error cases.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from treeviz.formats.parser import (
    register_format,
    get_supported_formats,
    get_format_by_name,
    detect_format,
    parse_document,
    _get_all_extensions,
    _FORMATS,
)
from treeviz.formats.model import Format, DocumentFormatError


class TestFormatRegistry:
    """Test format registration and discovery."""

    def setup_method(self):
        """Clear registry before each test."""
        _FORMATS.clear()

    def teardown_method(self):
        """Restore original formats after each test."""
        # Re-register built-in formats by re-importing the module
        import importlib
        import treeviz.formats.parser

        importlib.reload(treeviz.formats.parser)

    def test_register_format(self):
        """Test format registration."""

        def dummy_parser(content):
            return {"parsed": content}

        test_format = Format(
            name="Test",
            extensions=[".test"],
            parse_func=dummy_parser,
            description="Test format",
        )

        register_format(test_format)
        assert "test" in get_supported_formats()
        assert get_format_by_name("test") == test_format
        assert get_format_by_name("TEST") == test_format  # Case-insensitive

    def test_get_format_by_name_not_found(self):
        """Test getting format by name when not found."""
        result = get_format_by_name("nonexistent")
        assert result is None

    def test_detect_format_no_match(self):
        """Test format detection when no format can handle the file."""
        result = detect_format("file.unknown")
        assert result is None

    def test_get_all_extensions(self):
        """Test getting all supported extensions."""

        def dummy_parser(content):
            return content

        format1 = Format(
            "Test1", [".test1", ".t1"], dummy_parser, "Test format 1"
        )
        format2 = Format(
            "Test2", [".test2", ".t1"], dummy_parser, "Test format 2"
        )  # Duplicate .t1

        register_format(format1)
        register_format(format2)

        extensions = _get_all_extensions()
        assert ".test1" in extensions
        assert ".test2" in extensions
        assert ".t1" in extensions
        assert extensions.count(".t1") == 1  # Should be deduplicated
        assert extensions == sorted(extensions)  # Should be sorted


class TestParseDocument:
    """Test parse_document function error cases."""

    def test_parse_document_file_not_found(self):
        """Test FileNotFoundError when file doesn't exist."""
        with pytest.raises(
            FileNotFoundError, match="File not found: /nonexistent/file.json"
        ):
            parse_document("/nonexistent/file.json")

    def test_parse_document_unsupported_format_name(self):
        """Test DocumentFormatError for unsupported format name."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            with pytest.raises(
                DocumentFormatError, match="Unsupported format: nonexistent"
            ):
                parse_document(temp_path, format_name="nonexistent")
        finally:
            Path(temp_path).unlink()

    def test_parse_document_cannot_detect_format(self):
        """Test DocumentFormatError when format cannot be detected."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".unknown", delete=False
        ) as f:
            f.write("some content")
            temp_path = f.name

        try:
            with pytest.raises(
                DocumentFormatError, match="Cannot detect format for file"
            ):
                parse_document(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_document_unicode_decode_error(self):
        """Test DocumentFormatError for unicode decode errors."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".json", delete=False
        ) as f:
            # Write invalid UTF-8 bytes
            f.write(b'\xff\xfe{"invalid": "utf8"}')
            temp_path = f.name

        try:
            with pytest.raises(
                DocumentFormatError, match="Failed to read file as UTF-8"
            ):
                parse_document(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_document_with_valid_format_name(self):
        """Test parsing with explicit valid format name."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            # Should work even with non-json extension if we specify format
            result = parse_document(temp_path, format_name="json")
            assert result == {"test": "data"}
        finally:
            Path(temp_path).unlink()


class TestOptionalFormatImports:
    """Test optional format import error handling."""

    def test_yaml_import_error_handling(self):
        """Test YAML import error handling."""
        # This tests line 161-163 (except ImportError for YAML)
        with patch.dict("sys.modules", {"ruamel": None, "ruamel.yaml": None}):
            # Force re-import to trigger ImportError
            import importlib
            import treeviz.formats.parser

            importlib.reload(treeviz.formats.parser)

            # YAML should not be in supported formats
            supported = treeviz.formats.parser.get_supported_formats()
            assert "yaml" not in supported

    def test_html_import_error_handling(self):
        """Test HTML import error handling."""
        # This tests line 203-205 (except ImportError for HTML)
        with patch.dict("sys.modules", {"treeviz.formats.html_format": None}):
            # Force re-import to trigger ImportError
            import importlib
            import treeviz.formats.parser

            importlib.reload(treeviz.formats.parser)

            # HTML should not be in supported formats
            supported = treeviz.formats.parser.get_supported_formats()
            assert "html" not in supported


class TestFormatDetection:
    """Test format detection edge cases."""

    def test_detect_format_with_registered_formats(self):
        """Test format detection with actual registered formats."""
        # Clear and add a test format
        _FORMATS.clear()

        def dummy_parser(content):
            return content

        test_format = Format(
            name="TestFormat",
            extensions=[".test", ".tst"],
            parse_func=dummy_parser,
            description="Test format",
        )
        register_format(test_format)

        # Should detect the format
        detected = detect_format("file.test")
        assert detected == test_format

        detected = detect_format("file.tst")
        assert detected == test_format

        # Should not detect unknown extension
        detected = detect_format("file.unknown")
        assert detected is None


class TestBuiltInFormats:
    """Test that built-in formats are properly registered."""

    def test_json_format_registered(self):
        """Test that JSON format is registered by default."""
        # Re-import to ensure clean state
        import importlib
        import treeviz.formats.parser

        importlib.reload(treeviz.formats.parser)

        supported = treeviz.formats.parser.get_supported_formats()
        assert "json" in supported

        json_format = treeviz.formats.parser.get_format_by_name("json")
        assert json_format is not None
        assert ".json" in json_format.extensions
        assert ".jsonl" in json_format.extensions

    def test_pformat_format_registered(self):
        """Test that Pformat is registered by default."""
        # Re-import to ensure clean state
        import importlib
        import treeviz.formats.parser

        importlib.reload(treeviz.formats.parser)

        supported = treeviz.formats.parser.get_supported_formats()
        assert "pformat" in supported

        pformat_format = treeviz.formats.parser.get_format_by_name("pformat")
        assert pformat_format is not None
        assert ".pformat" in pformat_format.extensions
        assert ".pf" in pformat_format.extensions

    def test_xml_format_registered(self):
        """Test that XML format is registered by default."""
        # Re-import to ensure clean state
        import importlib
        import treeviz.formats.parser

        importlib.reload(treeviz.formats.parser)

        supported = treeviz.formats.parser.get_supported_formats()
        assert "xml" in supported

        xml_format = treeviz.formats.parser.get_format_by_name("xml")
        assert xml_format is not None
        assert ".xml" in xml_format.extensions
