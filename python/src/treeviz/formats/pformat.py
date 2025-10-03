"""
Optimized Pformat (Pseudo Document Format) parser.

This module implements a parser for XML-like document format that builds
dictionary structures directly during parsing, eliminating intermediate
node classes for better performance and maintainability.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union


class PformatParseError(Exception):
    """Exception raised when pformat parsing fails."""

    pass


class PformatParser:
    """
    Optimized parser for pformat (pseudo document format).

    Builds Python dict structures directly during parsing without
    intermediate node representations.
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
        self.element_stack: List[Tuple[str, Dict[str, Any]]] = []
        self.root_element: Optional[Dict[str, Any]] = None

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
        if self.root_element is None:
            raise PformatParseError("No root element found")

        if self.element_stack:
            unclosed = [tag for tag, _ in self.element_stack]
            raise PformatParseError(f"Unclosed tags: {', '.join(unclosed)}")

        return self.root_element

    def _parse_tags(self, tags: List[re.Match]) -> None:
        """Parse tag matches and build dict tree directly."""
        last_pos = 0

        for match in tags:
            # Handle text content before this tag
            text_before = self.content[last_pos : match.start()].strip()
            if text_before and self.element_stack:
                # Add text directly to current parent's children
                _, current_element = self.element_stack[-1]
                self._add_child(current_element, text_before)

            # Parse the tag
            self._parse_single_tag(match)
            last_pos = match.end()

        # Handle any remaining text
        remaining_text = self.content[last_pos:].strip()
        if remaining_text and self.element_stack:
            _, current_element = self.element_stack[-1]
            self._add_child(current_element, remaining_text)

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
        """Handle opening tag - create dict directly."""
        attributes = self._parse_attributes(attr_string)
        element = {
            "type": tag_name,
            **attributes,  # Include attributes as top-level properties
        }

        if self.element_stack:
            # Add to current parent's children
            _, parent_element = self.element_stack[-1]
            self._add_child(parent_element, element)
        else:
            # This is the root element
            if self.root_element is not None:
                raise PformatParseError("Multiple root elements found")
            self.root_element = element

        # Push to stack
        self.element_stack.append((tag_name, element))

    def _handle_closing_tag(self, tag_name: str) -> None:
        """Handle closing tag."""
        if not self.element_stack:
            raise PformatParseError(f"Unexpected closing tag: </{tag_name}>")

        expected_tag, current_element = self.element_stack[-1]
        if expected_tag != tag_name:
            raise PformatParseError(
                f"Mismatched tags: expected </{expected_tag}>, got </{tag_name}>"
            )

        # Finalize the element before popping
        self._finalize_element(current_element)

        # Pop from stack
        self.element_stack.pop()

    def _handle_self_closing_tag(self, tag_name: str, attr_string: str) -> None:
        """Handle self-closing tag - create dict directly."""
        attributes = self._parse_attributes(attr_string)
        element = {
            "type": tag_name,
            **attributes,  # Include attributes as top-level properties
            "self_closing": True,
        }

        if self.element_stack:
            # Add to current parent's children
            _, parent_element = self.element_stack[-1]
            self._add_child(parent_element, element)
        else:
            # This is the root element
            if self.root_element is not None:
                raise PformatParseError("Multiple root elements found")
            self.root_element = element

    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse attribute string into dict."""
        attributes = {}

        for match in self.ATTRIBUTE_PATTERN.finditer(attr_string):
            key = match.group(1)
            value = match.group(2)
            attributes[key] = value

        return attributes

    def _add_child(
        self, parent_element: Dict[str, Any], child: Union[str, Dict[str, Any]]
    ) -> None:
        """Add a child (text or element) to parent element."""
        if "children" not in parent_element:
            parent_element["children"] = []
        parent_element["children"].append(child)

    def _finalize_element(self, element: Dict[str, Any]) -> None:
        """Finalize element by setting text field for backward compatibility."""
        if "children" in element:
            # Extract text-only children for backward compatibility
            text_parts = [
                child for child in element["children"] if isinstance(child, str)
            ]
            if text_parts:
                combined_text = " ".join(text_parts).strip()
                if combined_text:
                    element["text"] = combined_text


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
