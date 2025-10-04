"""
Test XML format parsing functionality.

This module tests the XML parser implementation using xml.etree.ElementTree
including XML declarations, namespaces, and integration with the format system.
"""

import pytest
from pathlib import Path

from treeviz.formats.xml_format import parse_xml, XMLParseError
from treeviz.formats import parse_document, get_format_by_name


class TestXMLParser:
    """Test XML parser functionality."""

    def test_simple_xml_parsing(self):
        """Test parsing simple XML document."""
        content = "<root><child>content</child></root>"

        result = parse_xml(content)

        assert result["type"] == "root"
        assert len(result["children"]) == 1
        assert result["children"][0]["type"] == "child"
        assert result["children"][0]["text"] == "content"

    def test_xml_with_attributes(self):
        """Test parsing XML with attributes."""
        content = (
            '<book id="123" author="John Doe"><title>Sample</title></book>'
        )

        result = parse_xml(content)

        assert result["type"] == "book"
        assert result["id"] == "123"
        assert result["author"] == "John Doe"
        assert result["children"][0]["type"] == "title"
        assert result["children"][0]["text"] == "Sample"

    def test_xml_with_namespaces(self):
        """Test parsing XML with namespaces."""
        content = """
        <root xmlns:ns="http://example.com/namespace">
            <ns:element attr="value">content</ns:element>
        </root>
        """

        result = parse_xml(content)

        assert result["type"] == "root"
        # Namespace should be stripped from element name
        assert result["children"][0]["type"] == "element"
        assert result["children"][0]["attr"] == "value"
        assert result["children"][0]["text"] == "content"

    def test_xml_mixed_content(self):
        """Test XML with mixed text and element content."""
        content = "<p>text1 <b>bold</b> text2</p>"

        result = parse_xml(content)

        assert result["type"] == "p"
        # Should preserve order: text1, <b>bold</b>, text2
        assert len(result["children"]) == 3
        assert result["children"][0] == "text1"
        assert result["children"][1]["type"] == "b"
        assert result["children"][1]["text"] == "bold"
        assert result["children"][2] == "text2"

        # Combined text for compatibility
        assert result["text"] == "text1 text2"

    def test_xml_declaration_handling(self):
        """Test that XML declarations are handled properly."""
        content = '<?xml version="1.0" encoding="UTF-8"?><root>content</root>'

        result = parse_xml(content)

        assert result["type"] == "root"
        assert result["text"] == "content"

    def test_empty_xml_elements(self):
        """Test handling of empty XML elements."""
        content = "<root><empty/><another></another></root>"

        result = parse_xml(content)

        assert result["type"] == "root"
        assert len(result["children"]) == 2
        assert result["children"][0]["type"] == "empty"
        assert "children" not in result["children"][0]
        assert result["children"][1]["type"] == "another"

    def test_malformed_xml_error(self):
        """Test error handling for malformed XML."""
        content = "<root><unclosed></root>"

        with pytest.raises(XMLParseError) as exc_info:
            parse_xml(content)

        assert "Failed to parse XML" in str(exc_info.value)

    def test_invalid_xml_characters(self):
        """Test error handling for invalid XML characters."""
        content = "<root>text with invalid char \x00</root>"

        with pytest.raises(XMLParseError):
            parse_xml(content)


class TestXMLIntegration:
    """Test XML integration with format system."""

    def test_xml_format_registered(self):
        """Test that XML format is registered."""
        xml_format = get_format_by_name("xml")

        assert xml_format is not None
        assert xml_format.name == "XML"
        assert ".xml" in xml_format.extensions
        assert xml_format.description == "Extensible Markup Language"

    def test_parse_xml_file(self):
        """Test parsing XML file through format system."""
        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.xml"
        )

        result = parse_document(str(test_file))

        assert result["type"] == "book"
        assert result["id"] == "123"
        assert result["author"] == "John Doe"
        assert len(result["children"]) >= 2  # At least title and chapters

    def test_parse_xml_explicit_format(self):
        """Test parsing XML using explicit format specification."""
        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.xml"
        )

        result = parse_document(str(test_file), format_name="xml")

        assert result["type"] == "book"
        assert result["id"] == "123"
        assert result["author"] == "John Doe"

    def test_xml_vs_pformat_difference(self):
        """Test that XML parser handles features pformat doesn't."""
        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.xml"
        )

        # Parse as XML (should handle XML declaration)
        xml_result = parse_document(str(test_file), format_name="xml")

        # Parse as pformat (would ignore XML declaration and work differently)
        pformat_result = parse_document(str(test_file), format_name="pformat")

        # Both should parse successfully but potentially with different structures
        assert xml_result["type"] == "book"
        assert pformat_result["type"] == "book"

        # XML parser should be more accurate for XML-specific features
        assert xml_result["id"] == "123"
        assert xml_result["author"] == "John Doe"


class TestXMLWithAdapters:
    """Test XML integration with adapter system."""

    def test_xml_with_adapter(self):
        """Test complete workflow: XML -> adapter -> treeviz."""
        from treeviz.adapters import adapt_node

        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.xml"
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
        assert result.type == "book"
        assert len(result.children) >= 2  # Should have title and chapters

        # Find title element
        title_children = [
            child for child in result.children if child.type == "title"
        ]
        assert len(title_children) >= 1
        assert "Sample Book" in title_children[0].label

    def test_xml_with_children_selector(self):
        """Test XML with ChildrenSelector filtering."""
        from treeviz.adapters import adapt_node

        test_file = (
            Path(__file__).parent.parent.parent
            / "test-data"
            / "formats"
            / "simple.xml"
        )
        parsed_data = parse_document(str(test_file))

        # Filter to only include chapters
        adapter_def = {
            "label": "text",
            "type": "type",
            "children": {"include": ["chapter"], "exclude": ["title"]},
        }

        result = adapt_node(parsed_data, adapter_def)

        # Should only have chapters as children
        assert all(child.type == "chapter" for child in result.children)
        assert len(result.children) >= 2  # Should have at least 2 chapters
