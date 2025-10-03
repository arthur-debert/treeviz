"""
Pformat (Pseudo Document Format) parser.

This module implements a parser for XML-like document format with simple rules:
1. Root Element: Single root element containing all other elements
2. Nesting: Proper start/end tag nesting
3. Self-Closing Tags: Empty elements as <tag/>
4. Attributes: key="value" format with quoted values
5. Text Content: Text between start and end tags

This provides a foundation for parsing XML, HTML, and similar markup formats.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass


class PformatParseError(Exception):
    """Exception raised when pformat parsing fails."""

    pass


@dataclass
class PformatNode:
    """
    Internal representation of a pformat node.

    This gets converted to a Python dict structure that treeviz can process.
    """

    tag: str
    attributes: Dict[str, str]
    children: List[Union["PformatNode", "TextNode"]]
    is_self_closing: bool = False


@dataclass
class TextNode:
    """
    Internal representation of a text node.

    Represents text content that appears between element tags.
    """

    content: str


class PformatParser:
    """
    Parser for pformat (pseudo document format).

    Parses XML-like syntax into Python dict structures that can be
    processed by treeviz adapters.
    """

    # Regex patterns
    TAG_PATTERN = re.compile(r"<(/?)([a-zA-Z_][a-zA-Z0-9_\-]*)(.*?)(/?)>")
    ATTRIBUTE_PATTERN = re.compile(r'([a-zA-Z_][a-zA-Z0-9_\-]*)="([^"]*)"')

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset parser state."""
        self.position = 0
        self.content = ""
        self.tag_stack: List[Tuple[str, PformatNode]] = []
        self.root_node: Optional[PformatNode] = None

    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse pformat content into Python dict structure.

        Args:
            content: Pformat content to parse

        Returns:
            Python dict representing the document tree

        Raises:
            PformatParseError: If parsing fails
        """
        self.reset()
        self.content = content.strip()

        if not self.content:
            raise PformatParseError("Empty document")

        # Find all tags
        tags = list(self.TAG_PATTERN.finditer(self.content))
        if not tags:
            raise PformatParseError("No tags found in document")

        # Parse the document
        self._parse_tags(tags)

        # Ensure we have exactly one root element
        if self.root_node is None:
            raise PformatParseError("No root element found")

        if self.tag_stack:
            unclosed = [tag for tag, _ in self.tag_stack]
            raise PformatParseError(f"Unclosed tags: {', '.join(unclosed)}")

        # Convert to dict structure
        return self._node_to_dict(self.root_node)

    def _parse_tags(self, tags: List[re.Match]) -> None:
        """Parse tag matches and build node tree."""
        last_pos = 0

        for match in tags:
            # Handle text content before this tag
            text_before = self.content[last_pos : match.start()].strip()
            if text_before and self.tag_stack:
                # Add text as a separate TextNode to preserve order
                _, current_node = self.tag_stack[-1]
                text_node = TextNode(content=text_before)
                current_node.children.append(text_node)

            # Parse the tag
            self._parse_single_tag(match)
            last_pos = match.end()

        # Handle any remaining text
        remaining_text = self.content[last_pos:].strip()
        if remaining_text and self.tag_stack:
            _, current_node = self.tag_stack[-1]
            text_node = TextNode(content=remaining_text)
            current_node.children.append(text_node)

    def _parse_single_tag(self, match: re.Match) -> None:
        """Parse a single tag match."""
        is_closing = bool(match.group(1))  # "/" at start
        tag_name = match.group(2)
        attr_string = match.group(3)
        is_self_closing = bool(match.group(4))  # "/" at end

        if is_closing:
            # Closing tag
            self._handle_closing_tag(tag_name)
        elif is_self_closing:
            # Self-closing tag
            self._handle_self_closing_tag(tag_name, attr_string)
        else:
            # Opening tag
            self._handle_opening_tag(tag_name, attr_string)

    def _handle_opening_tag(self, tag_name: str, attr_string: str) -> None:
        """Handle opening tag."""
        attributes = self._parse_attributes(attr_string)
        node = PformatNode(tag=tag_name, attributes=attributes, children=[])

        if self.tag_stack:
            # Add to current parent's children
            _, parent_node = self.tag_stack[-1]
            parent_node.children.append(node)
        else:
            # This is the root element
            if self.root_node is not None:
                raise PformatParseError("Multiple root elements found")
            self.root_node = node

        # Push to stack
        self.tag_stack.append((tag_name, node))

    def _handle_closing_tag(self, tag_name: str) -> None:
        """Handle closing tag."""
        if not self.tag_stack:
            raise PformatParseError(f"Unexpected closing tag: </{tag_name}>")

        expected_tag, _ = self.tag_stack[-1]
        if expected_tag != tag_name:
            raise PformatParseError(
                f"Mismatched tags: expected </{expected_tag}>, got </{tag_name}>"
            )

        # Pop from stack
        self.tag_stack.pop()

    def _handle_self_closing_tag(self, tag_name: str, attr_string: str) -> None:
        """Handle self-closing tag."""
        attributes = self._parse_attributes(attr_string)
        node = PformatNode(
            tag=tag_name,
            attributes=attributes,
            children=[],
            is_self_closing=True,
        )

        if self.tag_stack:
            # Add to current parent's children
            _, parent_node = self.tag_stack[-1]
            parent_node.children.append(node)
        else:
            # This is the root element
            if self.root_node is not None:
                raise PformatParseError("Multiple root elements found")
            self.root_node = node

    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse attribute string into dict."""
        attributes = {}

        for match in self.ATTRIBUTE_PATTERN.finditer(attr_string):
            key = match.group(1)
            value = match.group(2)
            attributes[key] = value

        return attributes

    def _node_to_dict(
        self, node: Union[PformatNode, TextNode]
    ) -> Union[Dict[str, Any], str]:
        """Convert PformatNode or TextNode to dict structure."""
        if isinstance(node, TextNode):
            # Text nodes are represented as strings
            return node.content

        # Handle PformatNode
        result = {
            "type": node.tag,
            **node.attributes,  # Include attributes as top-level properties
        }

        # Process children - mix of elements and text nodes
        if node.children:
            converted_children = []
            text_parts = []

            for child in node.children:
                if isinstance(child, TextNode):
                    text_parts.append(child.content)
                else:
                    # If we have accumulated text, add it first
                    if text_parts:
                        # Only add non-empty combined text
                        combined_text = " ".join(text_parts).strip()
                        if combined_text:
                            converted_children.append(combined_text)
                        text_parts = []

                    # Add the element node
                    converted_children.append(self._node_to_dict(child))

            # Handle any remaining text at the end
            if text_parts:
                combined_text = " ".join(text_parts).strip()
                if combined_text:
                    converted_children.append(combined_text)

            # Set children if we have any
            if converted_children:
                result["children"] = converted_children

            # Also set text field for backward compatibility (combined text only)
            text_only_parts = [
                child.content
                for child in node.children
                if isinstance(child, TextNode)
            ]
            if text_only_parts:
                combined_text = " ".join(text_only_parts).strip()
                if combined_text:
                    result["text"] = combined_text

        # Add self-closing indicator if needed
        if node.is_self_closing:
            result["self_closing"] = True

        return result


def parse_pformat(content: str) -> Any:
    """
    Parse pformat content into Python object.

    Args:
        content: Pformat document content

    Returns:
        Python dict representing the document

    Raises:
        PformatParseError: If parsing fails
    """
    parser = PformatParser()
    return parser.parse(content)
