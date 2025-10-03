"""
Test HTML format parsing functionality.

This module tests the HTML parser implementation using BeautifulSoup4
including HTML-specific features and integration with the format system.
"""

import pytest
from pathlib import Path

from treeviz.formats.html_format import (
    parse_html,
    HTMLParseError,
    BS4_AVAILABLE,
)
from treeviz.formats import parse_document, get_format_by_name


class TestHTMLParser:
    """Test HTML parser functionality."""

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_simple_html_parsing(self):
        """Test parsing simple HTML document."""
        content = "<html><body><p>Hello World</p></body></html>"

        result = parse_html(content)

        assert result["type"] == "html"
        assert len(result["children"]) == 1
        assert result["children"][0]["type"] == "body"

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_html_with_attributes(self):
        """Test parsing HTML with attributes."""
        content = (
            '<div class="container" id="main"><p class="text">Content</p></div>'
        )

        result = parse_html(content)

        assert result["type"] == "div"
        assert result["class"] == "container"
        assert result["id"] == "main"
        assert result["children"][0]["type"] == "p"
        assert result["children"][0]["class"] == "text"

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_html_multiple_class_attributes(self):
        """Test HTML with multiple class values."""
        content = '<div class="container main-content active">Content</div>'

        result = parse_html(content)

        assert result["type"] == "div"
        # Multiple classes should be joined with spaces
        assert result["class"] == "container main-content active"

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_html_mixed_content(self):
        """Test HTML with mixed text and element content."""
        content = "<p>text1 <strong>bold</strong> text2</p>"

        result = parse_html(content)

        assert result["type"] == "p"
        # Should preserve order: text1, <strong>bold</strong>, text2
        assert len(result["children"]) == 3
        assert result["children"][0] == "text1"
        assert result["children"][1]["type"] == "strong"
        assert result["children"][1]["text"] == "bold"
        assert result["children"][2] == "text2"

        # Combined text for compatibility (only direct text, not from children)
        assert result["text"] == "text1 text2"

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_html_self_closing_tags(self):
        """Test HTML with self-closing tags."""
        content = (
            '<div><img src="image.jpg" alt="image"/><br/><p>Text</p></div>'
        )

        result = parse_html(content)

        assert result["type"] == "div"
        assert len(result["children"]) == 3

        # Check img tag
        img = result["children"][0]
        assert img["type"] == "img"
        assert img["src"] == "image.jpg"
        assert img["alt"] == "image"

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_html_doctype_handling(self):
        """Test that HTML DOCTYPE is handled properly."""
        content = "<!DOCTYPE html><html><head><title>Test</title></head><body>Content</body></html>"

        result = parse_html(content)

        assert result["type"] == "html"
        assert len(result["children"]) == 2  # head and body

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_malformed_html_tolerance(self):
        """Test that parser handles malformed HTML gracefully."""
        content = "<div><p>Unclosed paragraph<div>Nested div</div>"

        # Should not raise an error - BeautifulSoup handles malformed HTML
        result = parse_html(content)

        assert result["type"] == "div"
        # BeautifulSoup should fix the structure

    def test_html_without_bs4_error(self):
        """Test error when BeautifulSoup4 is not available."""
        if BS4_AVAILABLE:
            pytest.skip("BeautifulSoup4 is available, can't test this scenario")

        with pytest.raises(HTMLParseError) as exc_info:
            parse_html("<html><body>test</body></html>")

        assert "BeautifulSoup4 is required" in str(exc_info.value)

    @pytest.mark.skipif(
        not BS4_AVAILABLE, reason="BeautifulSoup4 not available"
    )
    def test_empty_html_error(self):
        """Test error handling for empty HTML."""
        content = "   "

        with pytest.raises(HTMLParseError) as exc_info:
            parse_html(content)

        assert "No HTML elements found" in str(exc_info.value)


@pytest.mark.skipif(not BS4_AVAILABLE, reason="BeautifulSoup4 not available")
class TestHTMLIntegration:
    """Test HTML integration with format system."""

    def test_html_format_registered(self):
        """Test that HTML format is registered."""
        html_format = get_format_by_name("html")

        if BS4_AVAILABLE:
            assert html_format is not None
            assert html_format.name == "HTML"
            assert ".html" in html_format.extensions
            assert ".htm" in html_format.extensions
            assert html_format.description == "HyperText Markup Language"
        else:
            # If BS4 not available, format shouldn't be registered
            assert html_format is None

    def test_parse_html_file(self):
        """Test parsing HTML file through format system."""
        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.html"
        )

        result = parse_document(str(test_file))

        assert result["type"] == "html"
        assert result["lang"] == "en"
        assert len(result["children"]) >= 2  # head and body

    def test_parse_html_explicit_format(self):
        """Test parsing HTML using explicit format specification."""
        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.html"
        )

        result = parse_document(str(test_file), format_name="html")

        assert result["type"] == "html"
        assert result["lang"] == "en"

    def test_html_vs_xml_vs_pformat_differences(self):
        """Test that HTML parser handles HTML-specific features better."""
        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.html"
        )

        # Parse as HTML
        html_result = parse_document(str(test_file), format_name="html")

        # Parse as XML (might fail on DOCTYPE or be stricter)
        try:
            parse_document(str(test_file), format_name="xml")
        except Exception:
            # Expected - XML parser might be stricter about HTML
            pass

        # Parse as pformat
        pformat_result = parse_document(str(test_file), format_name="pformat")

        # HTML parser should handle HTML best
        assert html_result["type"] == "html"
        assert html_result["lang"] == "en"

        # Pformat should also work but might not handle DOCTYPE
        assert pformat_result["type"] == "html"


@pytest.mark.skipif(not BS4_AVAILABLE, reason="BeautifulSoup4 not available")
class TestHTMLWithAdapters:
    """Test HTML integration with adapter system."""

    def test_html_with_adapter(self):
        """Test complete workflow: HTML -> adapter -> treeviz."""
        from treeviz.adapters.adapters import adapt_node

        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.html"
        )
        parsed_data = parse_document(str(test_file))

        # Apply adapter
        adapter_def = {
            "label": "text",  # Use text content as label
            "type": "type",  # Use type field
            "children": "children",
        }

        result = adapt_node(parsed_data, adapter_def)

        # Verify structure
        assert result.type == "html"
        assert len(result.children) >= 2  # Should have head and body

        # Find body element
        body_children = [
            child for child in result.children if child.type == "body"
        ]
        assert len(body_children) == 1

    def test_html_with_children_selector(self):
        """Test HTML with ChildrenSelector filtering."""
        from treeviz.adapters.adapters import adapt_node

        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.html"
        )
        parsed_data = parse_document(str(test_file))

        # Filter to only include specific elements
        adapter_def = {
            "label": "text",
            "type": "type",
            "children": {
                "include": ["head", "body"],
                "exclude": ["script", "style"],
            },
        }

        result = adapt_node(parsed_data, adapter_def)

        # Should have head and body
        child_types = {child.type for child in result.children}
        assert "head" in child_types
        assert "body" in child_types

        # Should not have script or style (if any existed)
        assert "script" not in child_types
        assert "style" not in child_types
