"""
Test pformat (Pseudo Document Format) parsing functionality.

This module tests the pformat parser implementation including XML-like
syntax parsing, attribute handling, and integration with the format system.
"""

import pytest

from treeviz.formats.pformat import (
    PformatParser,
    PformatParseError,
    parse_pformat,
    PformatNode,
)
from treeviz.formats import parse_document, get_format_by_name


class TestPformatNode:
    """Test PformatNode dataclass."""

    def test_pformat_node_creation(self):
        """Test basic PformatNode creation."""
        node = PformatNode(
            tag="test",
            attributes={"id": "123"},
            text_content="Test content",
            children=[],
        )

        assert node.tag == "test"
        assert node.attributes == {"id": "123"}
        assert node.text_content == "Test content"
        assert node.children == []
        assert node.is_self_closing is False

    def test_pformat_node_self_closing(self):
        """Test self-closing PformatNode."""
        node = PformatNode(
            tag="img",
            attributes={"src": "image.jpg"},
            text_content="",
            children=[],
            is_self_closing=True,
        )

        assert node.is_self_closing is True


class TestPformatParser:
    """Test PformatParser functionality."""

    def test_simple_document(self):
        """Test parsing simple document."""
        content = "<root>Simple content</root>"
        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "root"
        assert result["text"] == "Simple content"
        assert "children" not in result

    def test_nested_elements(self):
        """Test parsing nested elements."""
        content = """
        <document>
            <section>
                <paragraph>First paragraph</paragraph>
                <paragraph>Second paragraph</paragraph>
            </section>
        </document>
        """

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "document"
        assert len(result["children"]) == 1

        section = result["children"][0]
        assert section["type"] == "section"
        assert len(section["children"]) == 2

        assert section["children"][0]["type"] == "paragraph"
        assert section["children"][0]["text"] == "First paragraph"
        assert section["children"][1]["type"] == "paragraph"
        assert section["children"][1]["text"] == "Second paragraph"

    def test_attributes_parsing(self):
        """Test parsing element attributes."""
        content = '<book id="123" title="Sample Book" author="John Doe">Content</book>'

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "book"
        assert result["id"] == "123"
        assert result["title"] == "Sample Book"
        assert result["author"] == "John Doe"
        assert result["text"] == "Content"

    def test_self_closing_tags(self):
        """Test parsing self-closing tags."""
        content = """
        <document>
            <paragraph>Before image</paragraph>
            <img src="image.jpg" alt="Sample image"/>
            <paragraph>After image</paragraph>
        </document>
        """

        parser = PformatParser()
        result = parser.parse(content)

        assert len(result["children"]) == 3

        img = result["children"][1]
        assert img["type"] == "img"
        assert img["src"] == "image.jpg"
        assert img["alt"] == "Sample image"
        assert img["self_closing"] is True
        assert "text" not in img
        assert "children" not in img

    def test_mixed_content(self):
        """Test parsing mixed text and element content."""
        content = """
        <section name="test">
            Some text before
            <paragraph>Paragraph content</paragraph>
            Text between elements
            <paragraph>Another paragraph</paragraph>
            Final text
        </section>
        """

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "section"
        assert result["name"] == "test"
        # Mixed text content should be accumulated
        assert "Some text before" in result["text"]
        assert "Text between elements" in result["text"]
        assert "Final text" in result["text"]

        # Should have two paragraph children
        assert len(result["children"]) == 2
        assert result["children"][0]["text"] == "Paragraph content"
        assert result["children"][1]["text"] == "Another paragraph"

    def test_empty_document_error(self):
        """Test error handling for empty document."""
        parser = PformatParser()

        with pytest.raises(PformatParseError) as exc_info:
            parser.parse("")

        assert "Empty document" in str(exc_info.value)

    def test_no_tags_error(self):
        """Test error handling for document with no tags."""
        parser = PformatParser()

        with pytest.raises(PformatParseError) as exc_info:
            parser.parse("Just plain text with no tags")

        assert "No tags found in document" in str(exc_info.value)

    def test_unclosed_tag_error(self):
        """Test error handling for unclosed tags."""
        content = (
            "<document><section>Content without closing section</document>"
        )
        parser = PformatParser()

        with pytest.raises(PformatParseError) as exc_info:
            parser.parse(content)

        # This actually triggers mismatched tags error, which is correct
        assert "Mismatched tags" in str(exc_info.value)

    def test_mismatched_tags_error(self):
        """Test error handling for mismatched tags."""
        content = "<document><section>Content</paragraph></document>"
        parser = PformatParser()

        with pytest.raises(PformatParseError) as exc_info:
            parser.parse(content)

        assert "Mismatched tags" in str(exc_info.value)
        assert "expected </section>, got </paragraph>" in str(exc_info.value)

    def test_multiple_root_elements_error(self):
        """Test error handling for multiple root elements."""
        content = "<first>Content</first><second>More content</second>"
        parser = PformatParser()

        with pytest.raises(PformatParseError) as exc_info:
            parser.parse(content)

        assert "Multiple root elements found" in str(exc_info.value)

    def test_unexpected_closing_tag_error(self):
        """Test error handling for unexpected closing tag."""
        content = "</unexpected>"
        parser = PformatParser()

        with pytest.raises(PformatParseError) as exc_info:
            parser.parse(content)

        assert "Unexpected closing tag" in str(exc_info.value)

    def test_complex_attributes(self):
        """Test parsing complex attribute combinations."""
        content = '<element id="test-123" class="main-content" data-value="special chars: !@#$%">Content</element>'

        parser = PformatParser()
        result = parser.parse(content)

        assert result["id"] == "test-123"
        assert result["class"] == "main-content"
        assert result["data-value"] == "special chars: !@#$%"

    def test_self_closing_as_root(self):
        """Test self-closing tag as root element."""
        content = '<config setting="test" value="123"/>'

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "config"
        assert result["setting"] == "test"
        assert result["value"] == "123"
        assert result["self_closing"] is True


class TestPformatFunction:
    """Test parse_pformat function."""

    def test_parse_pformat_function(self):
        """Test the standalone parse_pformat function."""
        content = '<doc title="Test">Content here</doc>'

        result = parse_pformat(content)

        assert result["type"] == "doc"
        assert result["title"] == "Test"
        assert result["text"] == "Content here"

    def test_parse_pformat_error_propagation(self):
        """Test that errors are properly propagated."""
        with pytest.raises(PformatParseError):
            parse_pformat("<unclosed>")


class TestPformatIntegration:
    """Test pformat integration with format system."""

    def test_pformat_registered(self):
        """Test that pformat is registered in format system."""
        pformat_format = get_format_by_name("pformat")

        assert pformat_format is not None
        assert pformat_format.name == "Pformat"
        assert ".pformat" in pformat_format.extensions
        assert ".pf" in pformat_format.extensions

    def test_parse_pformat_file(self):
        """Test parsing pformat file through format system."""
        test_file = "/Users/adebert/h/treeviz/test-data/formats/sample.pformat"

        result = parse_document(test_file)

        assert result["type"] == "document"
        assert result["title"] == "Sample Document"
        assert result["version"] == "1.0"
        assert len(result["children"]) == 3  # 2 sections + footer

    def test_parse_xml_file_as_pformat(self):
        """Test parsing XML file using pformat parser."""
        test_file = "/Users/adebert/h/treeviz/test-data/formats/simple.xml"

        # Parse as pformat explicitly
        result = parse_document(test_file, format_name="pformat")

        assert result["type"] == "book"  # Ignores XML declaration
        assert result["id"] == "123"
        assert result["author"] == "John Doe"

    def test_parse_malformed_pformat(self):
        """Test error handling with malformed pformat file."""
        test_file = (
            "/Users/adebert/h/treeviz/test-data/formats/malformed.pformat"
        )

        with pytest.raises(Exception) as exc_info:
            parse_document(test_file)

        # Should get a DocumentFormatError wrapping PformatParseError
        assert "Failed to parse content as Pformat" in str(exc_info.value)


class TestPformatWithAdapters:
    """Test pformat integration with adapter system."""

    def test_pformat_with_adapter(self):
        """Test complete workflow: pformat -> adapter -> treeviz."""
        from treeviz.adapters.adapters import adapt_node

        # Parse pformat document
        test_file = "/Users/adebert/h/treeviz/test-data/formats/sample.pformat"
        parsed_data = parse_document(test_file)

        # Apply adapter
        adapter_def = {
            "label": "name",  # Extract name attribute as label
            "type": "type",  # Use type field
            "children": "children",
        }

        result = adapt_node(parsed_data, adapter_def)

        # Verify structure
        assert result.type == "document"
        assert len(result.children) == 3

        # Check sections have proper labels
        sections = [
            child for child in result.children if child.type == "section"
        ]
        assert len(sections) == 2
        assert sections[0].label == "Introduction"
        assert sections[1].label == "Content"

    def test_pformat_with_children_selector(self):
        """Test pformat with ChildrenSelector from issue #9."""
        from treeviz.adapters.adapters import adapt_node

        test_file = "/Users/adebert/h/treeviz/test-data/formats/sample.pformat"
        parsed_data = parse_document(test_file)

        # Use ChildrenSelector to filter only sections
        adapter_def = {
            "label": "name",
            "type": "type",
            "children": {"include": ["section"], "exclude": ["footer"]},
        }

        result = adapt_node(parsed_data, adapter_def)

        # Should only have sections, no footer
        assert len(result.children) == 2
        assert all(child.type == "section" for child in result.children)

    def test_xml_html_pformat_equivalence(self):
        """Test that XML and HTML can be parsed via pformat."""
        from treeviz.adapters.adapters import adapt_node

        # Parse different formats with same adapter
        adapter_def = {
            "label": "text",  # Use text content as label
            "type": "type",
            "children": "children",
        }

        # Parse pformat
        pformat_data = parse_document(
            "/Users/adebert/h/treeviz/test-data/formats/sample.pformat"
        )
        pformat_result = adapt_node(pformat_data, adapter_def)

        # Parse XML via pformat
        xml_data = parse_document(
            "/Users/adebert/h/treeviz/test-data/formats/simple.xml",
            format_name="pformat",
        )
        xml_result = adapt_node(xml_data, adapter_def)

        # Both should work (though with different content)
        assert pformat_result.type == "document"
        assert xml_result.type == "book"
        assert len(pformat_result.children) > 0
        assert len(xml_result.children) > 0
