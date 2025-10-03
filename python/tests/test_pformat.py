"""
Test pformat (Pseudo Document Format) parsing functionality.

This module tests the pformat parser implementation including XML-like
syntax parsing, attribute handling, and integration with the format system.
"""

import pytest
from pathlib import Path

from treeviz.formats.pformat import (
    PformatParser,
    PformatParseError,
    parse_pformat,
)
from treeviz.formats import parse_document, get_format_by_name


def get_test_data_path(filename: str) -> str:
    """Get path to test data file."""
    return str(
        Path(__file__).parent.parent.parent / "test-data" / "formats" / filename
    )


class TestPformatParser:
    """Test PformatParser functionality."""

    def test_simple_document(self):
        """Test parsing simple document."""
        content = "<root>Simple content</root>"
        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "root"
        assert result["text"] == "Simple content"
        # Now children contains the text node
        assert len(result["children"]) == 1
        assert result["children"][0] == "Simple content"

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
        # Mixed text content should be accumulated in text field for compatibility
        assert "Some text before" in result["text"]
        assert "Text between elements" in result["text"]
        assert "Final text" in result["text"]

        # Should now have 5 children preserving document order: text, element, text, element, text
        assert len(result["children"]) == 5
        assert result["children"][0] == "Some text before"  # Text node
        assert result["children"][1]["type"] == "paragraph"  # Element node
        assert result["children"][1]["text"] == "Paragraph content"
        assert result["children"][2] == "Text between elements"  # Text node
        assert result["children"][3]["type"] == "paragraph"  # Element node
        assert result["children"][3]["text"] == "Another paragraph"
        assert result["children"][4] == "Final text"  # Text node

    def test_attributes_with_empty_values(self):
        """Test parsing attributes with empty values."""
        content = (
            '<element attr="" empty-attr="" class="non-empty">Content</element>'
        )

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "element"
        assert result["attr"] == ""  # Empty string should be preserved
        assert result["empty-attr"] == ""
        assert result["class"] == "non-empty"
        assert result["text"] == "Content"

    def test_tags_with_hyphens_and_numbers(self):
        """Test parsing tags with hyphens and numbers in names."""
        content = """
        <html-5>
            <custom-element-123>
                <data-item-001 data-value="test">Content</data-item-001>
            </custom-element-123>
            <tag2>Another tag</tag2>
        </html-5>
        """

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "html-5"
        assert len(result["children"]) == 2

        # Check custom element with hyphens and numbers
        custom_element = result["children"][0]
        assert custom_element["type"] == "custom-element-123"

        # Check nested data item
        data_item = custom_element["children"][0]
        assert data_item["type"] == "data-item-001"
        assert data_item["data-value"] == "test"
        assert data_item["text"] == "Content"

        # Check tag with number
        tag2 = result["children"][1]
        assert tag2["type"] == "tag2"
        assert tag2["text"] == "Another tag"

    def test_deep_nesting_scenario(self):
        """Test parsing deeply nested elements."""
        content = """
        <level1 id="1">
            <level2 id="2">
                <level3 id="3">
                    <level4 id="4">
                        <level5 id="5">
                            Deep content here
                            <span>With inline element</span>
                            And more text
                        </level5>
                    </level4>
                </level3>
            </level2>
        </level1>
        """

        parser = PformatParser()
        result = parser.parse(content)

        # Navigate down the nesting
        current = result
        for level in range(1, 6):
            assert current["type"] == f"level{level}"
            assert current["id"] == str(level)
            if level < 5:
                assert len(current["children"]) == 1
                current = current["children"][0]

        # Check the deepest level has mixed content
        level5 = current
        assert len(level5["children"]) == 3  # text, span, text
        assert level5["children"][0] == "Deep content here"
        assert level5["children"][1]["type"] == "span"
        assert level5["children"][1]["text"] == "With inline element"
        assert level5["children"][2] == "And more text"

    def test_attributes_with_special_characters(self):
        """Test parsing attributes with various special characters."""
        content = '<element id="test-123" class="main content active" data-value="special chars: !@#$%^&*()" aria-label="Multi-word label with spaces" custom="value with quotes">Content</element>'

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "element"
        assert result["id"] == "test-123"
        assert result["class"] == "main content active"
        assert result["data-value"] == "special chars: !@#$%^&*()"
        assert result["aria-label"] == "Multi-word label with spaces"
        assert result["custom"] == "value with quotes"
        assert result["text"] == "Content"

    def test_mixed_self_closing_and_regular_tags(self):
        """Test complex mix of self-closing and regular tags."""
        content = """
        <document version="2.0">
            <metadata>
                <author>John Doe</author>
                <created date="2024-01-01"/>
                <tags>
                    <tag value="important"/>
                    <tag value="draft"/>
                </tags>
            </metadata>
            <content>
                <section title="Introduction">
                    <p>This is a paragraph.</p>
                    <br/>
                    <p>Another paragraph after break.</p>
                    <img src="diagram.png" alt="Flow diagram"/>
                </section>
            </content>
        </document>
        """

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "document"
        assert result["version"] == "2.0"
        assert len(result["children"]) == 2  # metadata and content

        # Check metadata section
        metadata = result["children"][0]
        assert metadata["type"] == "metadata"
        assert len(metadata["children"]) == 3  # author, created, tags

        # Check self-closing created tag
        created = metadata["children"][1]
        assert created["type"] == "created"
        assert created["date"] == "2024-01-01"
        assert created["self_closing"] is True

        # Check tags with multiple self-closing children
        tags = metadata["children"][2]
        assert tags["type"] == "tags"
        assert len(tags["children"]) == 2
        for i, tag in enumerate(tags["children"]):
            assert tag["type"] == "tag"
            assert tag["self_closing"] is True
            assert tag["value"] in ["important", "draft"]

    def test_whitespace_handling(self):
        """Test handling of various whitespace scenarios."""
        content = """
        
        <root>
            
            <child>   Text with spaces   </child>
            
            <empty>    </empty>
            
            <mixed>
                Text before
                <sub>nested</sub>
                Text after
            </mixed>
            
        </root>
        
        """

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "root"
        assert len(result["children"]) == 3

        # Check child with spaces in text
        child = result["children"][0]
        assert child["type"] == "child"
        assert child["text"] == "Text with spaces"  # Should be trimmed

        # Check empty element with only whitespace (should have no text)
        empty = result["children"][1]
        assert empty["type"] == "empty"
        assert "text" not in empty or empty.get("text") == ""

        # Check mixed content with whitespace
        mixed = result["children"][2]
        assert mixed["type"] == "mixed"
        assert len(mixed["children"]) == 3
        assert mixed["children"][0] == "Text before"
        assert mixed["children"][1]["type"] == "sub"
        assert mixed["children"][2] == "Text after"

    def test_mixed_content_preserves_order(self):
        """Test that mixed content preserves document order - addresses GitHub comment issue."""
        content = "<p>text1 <b>bold</b> text2</p>"

        parser = PformatParser()
        result = parser.parse(content)

        assert result["type"] == "p"
        # Should have 3 children in correct order: text1, <b>bold</b>, text2
        assert len(result["children"]) == 3
        assert result["children"][0] == "text1"  # Text before bold
        assert result["children"][1]["type"] == "b"  # Bold element
        assert result["children"][1]["text"] == "bold"
        assert (
            result["children"][2] == "text2"
        )  # Text after bold - this was lost before!

        # Backward compatibility: text field still contains all text
        assert result["text"] == "text1 text2"

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
        test_file = get_test_data_path("sample.pformat")

        result = parse_document(test_file)

        assert result["type"] == "document"
        assert result["title"] == "Sample Document"
        assert result["version"] == "1.0"
        assert len(result["children"]) == 3  # 2 sections + footer

    def test_parse_xml_file_as_pformat(self):
        """Test parsing XML file using pformat parser."""
        test_file = get_test_data_path("simple.xml")

        # Parse as pformat explicitly
        result = parse_document(test_file, format_name="pformat")

        assert result["type"] == "book"  # Ignores XML declaration
        assert result["id"] == "123"
        assert result["author"] == "John Doe"

    def test_parse_malformed_pformat(self):
        """Test error handling with malformed pformat file."""
        test_file = get_test_data_path("malformed.pformat")

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
        test_file = get_test_data_path("sample.pformat")
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

        test_file = get_test_data_path("sample.pformat")
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
        pformat_data = parse_document(get_test_data_path("sample.pformat"))
        pformat_result = adapt_node(pformat_data, adapter_def)

        # Parse XML via pformat
        xml_data = parse_document(
            get_test_data_path("simple.xml"),
            format_name="pformat",
        )
        xml_result = adapt_node(xml_data, adapter_def)

        # Both should work (though with different content)
        assert pformat_result.type == "document"
        assert xml_result.type == "book"
        assert len(pformat_result.children) > 0
        assert len(xml_result.children) > 0
