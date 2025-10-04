"""
Unit tests for pformat (pseudo document format) parser.

Tests the XML-like document parser for various edge cases, error conditions,
and normal parsing scenarios.
"""

import pytest
from unittest.mock import Mock, patch

from treeviz.formats.pformat_original import (
    PformatParser,
    PformatNode,
    TextNode,
    PformatParseError,
    parse_pformat,
)


class TestPformatParseError:
    """Test PformatParseError exception class."""

    def test_parse_error_creation(self):
        """Test creating PformatParseError."""
        error = PformatParseError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestPformatNode:
    """Test PformatNode dataclass."""

    def test_node_creation(self):
        """Test creating PformatNode with defaults."""
        node = PformatNode(tag="div", attributes={}, children=[])
        assert node.tag == "div"
        assert node.attributes == {}
        assert node.children == []
        assert node.is_self_closing is False

    def test_node_self_closing(self):
        """Test creating self-closing PformatNode."""
        node = PformatNode(
            tag="br",
            attributes={"id": "test"},
            children=[],
            is_self_closing=True,
        )
        assert node.tag == "br"
        assert node.attributes == {"id": "test"}
        assert node.is_self_closing is True


class TestTextNode:
    """Test TextNode dataclass."""

    def test_text_node_creation(self):
        """Test creating TextNode."""
        text_node = TextNode(content="Hello world")
        assert text_node.content == "Hello world"


class TestPformatParserInit:
    """Test PformatParser initialization and reset."""

    def test_parser_init(self):
        """Test parser initialization."""
        parser = PformatParser()
        assert parser.position == 0
        assert parser.content == ""
        assert parser.tag_stack == []
        assert parser.root_node is None

    def test_parser_reset(self):
        """Test parser reset functionality."""
        parser = PformatParser()
        # Modify state
        parser.position = 10
        parser.content = "test"
        parser.tag_stack = [("test", Mock())]
        parser.root_node = Mock()

        # Reset should clear everything
        parser.reset()
        assert parser.position == 0
        assert parser.content == ""
        assert parser.tag_stack == []
        assert parser.root_node is None


class TestPformatParserParseBasic:
    """Test basic parsing functionality."""

    def test_parse_empty_document_error(self):
        """Test parsing empty document raises error."""
        parser = PformatParser()
        with pytest.raises(PformatParseError, match="Empty document"):
            parser.parse("")

    def test_parse_whitespace_only_document_error(self):
        """Test parsing whitespace-only document raises error."""
        parser = PformatParser()
        with pytest.raises(PformatParseError, match="Empty document"):
            parser.parse("   \n\t  ")

    def test_parse_no_tags_error(self):
        """Test parsing document with no tags raises error."""
        parser = PformatParser()
        with pytest.raises(
            PformatParseError, match="No tags found in document"
        ):
            parser.parse("Just plain text with no tags")

    def test_parse_simple_self_closing_tag(self):
        """Test parsing simple self-closing tag."""
        parser = PformatParser()
        result = parser.parse("<br/>")

        expected = {"type": "br", "self_closing": True}
        assert result == expected

    def test_parse_simple_element_with_text(self):
        """Test parsing simple element with text content."""
        parser = PformatParser()
        result = parser.parse("<p>Hello world</p>")

        expected = {
            "type": "p",
            "children": ["Hello world"],
            "text": "Hello world",
        }
        assert result == expected

    def test_parse_nested_elements(self):
        """Test parsing nested elements."""
        parser = PformatParser()
        result = parser.parse("<div><p>Hello</p></div>")

        expected = {
            "type": "div",
            "children": [{"type": "p", "children": ["Hello"], "text": "Hello"}],
        }
        assert result == expected


class TestPformatParserAttributes:
    """Test attribute parsing functionality."""

    def test_parse_element_with_attributes(self):
        """Test parsing element with attributes."""
        parser = PformatParser()
        result = parser.parse('<div id="test" class="container">Content</div>')

        expected = {
            "type": "div",
            "id": "test",
            "class": "container",
            "children": ["Content"],
            "text": "Content",
        }
        assert result == expected

    def test_parse_self_closing_with_attributes(self):
        """Test parsing self-closing tag with attributes."""
        parser = PformatParser()
        result = parser.parse('<img src="test.jpg" alt="Test image"/>')

        expected = {
            "type": "img",
            "src": "test.jpg",
            "alt": "Test image",
            "self_closing": True,
        }
        assert result == expected

    def test_parse_attributes_internal_method(self):
        """Test _parse_attributes method directly."""
        parser = PformatParser()

        # Test empty attributes
        result = parser._parse_attributes("")
        assert result == {}

        # Test single attribute
        result = parser._parse_attributes(' id="test"')
        assert result == {"id": "test"}

        # Test multiple attributes
        result = parser._parse_attributes(
            ' id="test" class="container" data-value="123"'
        )
        assert result == {
            "id": "test",
            "class": "container",
            "data-value": "123",
        }


class TestPformatParserErrorCases:
    """Test error handling scenarios."""

    def test_parse_multiple_root_elements_error(self):
        """Test error when multiple root elements are found."""
        parser = PformatParser()
        with pytest.raises(
            PformatParseError, match="Multiple root elements found"
        ):
            parser.parse("<div></div><span></span>")

    def test_parse_multiple_root_self_closing_error(self):
        """Test error when multiple root self-closing elements are found."""
        parser = PformatParser()
        with pytest.raises(
            PformatParseError, match="Multiple root elements found"
        ):
            parser.parse("<br/><hr/>")

    def test_parse_unclosed_tags_error(self):
        """Test error when tags are not properly closed."""
        parser = PformatParser()
        with pytest.raises(PformatParseError, match="Unclosed tags: div, p"):
            parser.parse("<div><p>Unclosed")

    def test_parse_unexpected_closing_tag_error(self):
        """Test error when unexpected closing tag is found."""
        parser = PformatParser()
        with pytest.raises(
            PformatParseError, match="Unexpected closing tag: </div>"
        ):
            parser.parse("</div>")

    def test_parse_mismatched_tags_error(self):
        """Test error when tags don't match."""
        parser = PformatParser()
        with pytest.raises(
            PformatParseError,
            match="Mismatched tags: expected </div>, got </span>",
        ):
            parser.parse("<div></span>")

    def test_parse_no_root_element_error(self):
        """Test error when no root element is found."""
        parser = PformatParser()
        # Mock _parse_tags to not set root_node
        with patch.object(parser, "_parse_tags"):
            with pytest.raises(
                PformatParseError, match="No root element found"
            ):
                parser.parse("<test>content</test>")


class TestPformatParserComplexDocuments:
    """Test parsing complex document structures."""

    def test_parse_mixed_content(self):
        """Test parsing elements with mixed text and element children."""
        parser = PformatParser()
        result = parser.parse("<div>Before <span>inside</span> after</div>")

        expected = {
            "type": "div",
            "children": [
                "Before",
                {"type": "span", "children": ["inside"], "text": "inside"},
                "after",
            ],
            "text": "Before after",
        }
        assert result == expected

    def test_parse_deeply_nested(self):
        """Test parsing deeply nested elements."""
        parser = PformatParser()
        result = parser.parse("<a><b><c>Deep</c></b></a>")

        expected = {
            "type": "a",
            "children": [
                {
                    "type": "b",
                    "children": [
                        {"type": "c", "children": ["Deep"], "text": "Deep"}
                    ],
                }
            ],
        }
        assert result == expected

    def test_parse_multiple_text_nodes(self):
        """Test parsing with multiple text nodes that get combined."""
        parser = PformatParser()
        # Create content that will have multiple text parts
        result = parser.parse("<div>  First   Second  </div>")

        expected = {
            "type": "div",
            "children": ["First   Second"],
            "text": "First   Second",
        }
        assert result == expected

    def test_parse_siblings_with_text(self):
        """Test parsing sibling elements with text."""
        parser = PformatParser()
        result = parser.parse("<div><p>Para1</p><p>Para2</p></div>")

        expected = {
            "type": "div",
            "children": [
                {"type": "p", "children": ["Para1"], "text": "Para1"},
                {"type": "p", "children": ["Para2"], "text": "Para2"},
            ],
        }
        assert result == expected


class TestPformatParserTextHandling:
    """Test text content handling."""

    def test_parse_element_text_only(self):
        """Test element with only text content."""
        parser = PformatParser()
        result = parser.parse("<span>Just text</span>")

        expected = {
            "type": "span",
            "children": ["Just text"],
            "text": "Just text",
        }
        assert result == expected

    def test_parse_empty_element(self):
        """Test empty element (no content between tags)."""
        parser = PformatParser()
        result = parser.parse("<div></div>")

        expected = {"type": "div"}
        assert result == expected

    def test_parse_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        parser = PformatParser()
        result = parser.parse("<p>   Trimmed text   </p>")

        expected = {
            "type": "p",
            "children": ["Trimmed text"],
            "text": "Trimmed text",
        }
        assert result == expected


class TestPformatParserNodeToDict:
    """Test _node_to_dict method functionality."""

    def test_node_to_dict_text_node(self):
        """Test converting TextNode to dict."""
        parser = PformatParser()
        text_node = TextNode(content="Test text")
        result = parser._node_to_dict(text_node)
        assert result == "Test text"

    def test_node_to_dict_simple_element(self):
        """Test converting simple PformatNode to dict."""
        parser = PformatParser()
        node = PformatNode(tag="div", attributes={"id": "test"}, children=[])
        result = parser._node_to_dict(node)

        expected = {"type": "div", "id": "test"}
        assert result == expected

    def test_node_to_dict_self_closing(self):
        """Test converting self-closing node to dict."""
        parser = PformatParser()
        node = PformatNode(
            tag="br", attributes={}, children=[], is_self_closing=True
        )
        result = parser._node_to_dict(node)

        expected = {"type": "br", "self_closing": True}
        assert result == expected

    def test_node_to_dict_with_children_mixed(self):
        """Test converting node with mixed children (text and elements)."""
        parser = PformatParser()

        child_node = PformatNode(tag="span", attributes={}, children=[])
        text_node = TextNode(content="text")

        node = PformatNode(
            tag="div", attributes={}, children=[text_node, child_node]
        )
        result = parser._node_to_dict(node)

        expected = {
            "type": "div",
            "children": ["text", {"type": "span"}],
            "text": "text",
        }
        assert result == expected


class TestPformatParserTagHandling:
    """Test individual tag handling methods."""

    def test_handle_opening_tag_as_root(self):
        """Test handling opening tag as root element."""
        parser = PformatParser()
        parser._handle_opening_tag("div", ' id="test"')

        assert parser.root_node is not None
        assert parser.root_node.tag == "div"
        assert parser.root_node.attributes == {"id": "test"}
        assert len(parser.tag_stack) == 1

    def test_handle_opening_tag_as_child(self):
        """Test handling opening tag as child element."""
        parser = PformatParser()
        # Set up parent first
        parent = PformatNode(tag="div", attributes={}, children=[])
        parser.tag_stack.append(("div", parent))

        parser._handle_opening_tag("span", "")

        assert len(parent.children) == 1
        assert parent.children[0].tag == "span"
        assert len(parser.tag_stack) == 2

    def test_handle_closing_tag_success(self):
        """Test successful closing tag handling."""
        parser = PformatParser()
        node = PformatNode(tag="div", attributes={}, children=[])
        parser.tag_stack.append(("div", node))

        parser._handle_closing_tag("div")

        assert len(parser.tag_stack) == 0

    def test_handle_closing_tag_empty_stack_error(self):
        """Test closing tag with empty stack raises error."""
        parser = PformatParser()

        with pytest.raises(
            PformatParseError, match="Unexpected closing tag: </div>"
        ):
            parser._handle_closing_tag("div")

    def test_handle_closing_tag_mismatch_error(self):
        """Test mismatched closing tag raises error."""
        parser = PformatParser()
        node = PformatNode(tag="div", attributes={}, children=[])
        parser.tag_stack.append(("div", node))

        with pytest.raises(
            PformatParseError,
            match="Mismatched tags: expected </div>, got </span>",
        ):
            parser._handle_closing_tag("span")

    def test_handle_self_closing_tag_as_root(self):
        """Test handling self-closing tag as root."""
        parser = PformatParser()
        parser._handle_self_closing_tag("br", "")

        assert parser.root_node is not None
        assert parser.root_node.tag == "br"
        assert parser.root_node.is_self_closing is True
        assert len(parser.tag_stack) == 0  # Self-closing tags don't go on stack

    def test_handle_self_closing_tag_as_child(self):
        """Test handling self-closing tag as child."""
        parser = PformatParser()
        parent = PformatNode(tag="div", attributes={}, children=[])
        parser.tag_stack.append(("div", parent))

        parser._handle_self_closing_tag("br", "")

        assert len(parent.children) == 1
        assert parent.children[0].tag == "br"
        assert parent.children[0].is_self_closing is True


class TestPformatParserRegexPatterns:
    """Test regex pattern matching."""

    def test_tag_pattern_matching(self):
        """Test TAG_PATTERN regex matching various tag formats."""
        pattern = PformatParser.TAG_PATTERN

        # Opening tag
        match = pattern.search("<div>")
        assert match.groups() == ("", "div", "", "")

        # Closing tag
        match = pattern.search("</div>")
        assert match.groups() == ("/", "div", "", "")

        # Self-closing tag
        match = pattern.search("<br/>")
        assert match.groups() == ("", "br", "", "/")

        # Tag with attributes
        match = pattern.search('<div id="test">')
        assert match.groups() == ("", "div", ' id="test"', "")

    def test_attribute_pattern_matching(self):
        """Test ATTRIBUTE_PATTERN regex matching."""
        pattern = PformatParser.ATTRIBUTE_PATTERN

        # Single attribute
        matches = list(pattern.finditer('id="test"'))
        assert len(matches) == 1
        assert matches[0].groups() == ("id", "test")

        # Multiple attributes
        matches = list(pattern.finditer('id="test" class="container"'))
        assert len(matches) == 2
        assert matches[0].groups() == ("id", "test")
        assert matches[1].groups() == ("class", "container")


class TestParsePformatFunction:
    """Test the standalone parse_pformat function."""

    def test_parse_pformat_function(self):
        """Test parse_pformat function creates parser and parses."""
        result = parse_pformat("<div>Hello</div>")

        expected = {"type": "div", "children": ["Hello"], "text": "Hello"}
        assert result == expected

    def test_parse_pformat_function_error_propagation(self):
        """Test that parse_pformat propagates parsing errors."""
        with pytest.raises(PformatParseError, match="Empty document"):
            parse_pformat("")


class TestPformatParserEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_parse_tags_text_accumulation(self):
        """Test text accumulation in _parse_tags method."""
        parser = PformatParser()
        # This tests the path where multiple text nodes are accumulated and combined
        result = parser.parse("<div>Start <em>middle</em> end</div>")

        # The text "Start" and "end" should be preserved as separate children
        expected = {
            "type": "div",
            "children": [
                "Start",
                {"type": "em", "children": ["middle"], "text": "middle"},
                "end",
            ],
            "text": "Start end",
        }
        assert result == expected

    def test_multiple_root_opening_tag_error(self):
        """Test error when trying to set multiple root elements via opening tags."""
        parser = PformatParser()
        # Manually set a root to test the error path
        parser.root_node = PformatNode(
            tag="existing", attributes={}, children=[]
        )

        with pytest.raises(
            PformatParseError, match="Multiple root elements found"
        ):
            parser._handle_opening_tag("new", "")

    def test_multiple_root_self_closing_tag_error(self):
        """Test error when trying to set multiple root elements via self-closing tags."""
        parser = PformatParser()
        # Manually set a root to test the error path
        parser.root_node = PformatNode(
            tag="existing", attributes={}, children=[]
        )

        with pytest.raises(
            PformatParseError, match="Multiple root elements found"
        ):
            parser._handle_self_closing_tag("new", "")

    def test_tag_name_variations(self):
        """Test various valid tag name formats."""
        parser = PformatParser()

        # Test underscore and dash in tag names
        result = parser.parse("<my_tag-name>content</my_tag-name>")
        expected = {
            "type": "my_tag-name",
            "children": ["content"],
            "text": "content",
        }
        assert result == expected

    def test_complex_attribute_values(self):
        """Test complex attribute values with special characters."""
        parser = PformatParser()
        result = parser.parse(
            '<div data-test="value with spaces" title="Special & chars">content</div>'
        )

        expected = {
            "type": "div",
            "data-test": "value with spaces",
            "title": "Special & chars",
            "children": ["content"],
            "text": "content",
        }
        assert result == expected
