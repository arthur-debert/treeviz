"""
HTML format parser using BeautifulSoup4.

This module provides robust HTML parsing using BeautifulSoup4,
which handles malformed HTML and various HTML-specific features.
"""

from typing import Dict, Any
from bs4 import BeautifulSoup, NavigableString, Tag


class HTMLParseError(Exception):
    """Exception raised when HTML parsing fails."""

    pass


def parse_html(content: str) -> Dict[str, Any]:
    """
    Parse HTML content into Python dict structure.

    Args:
        content: HTML document content

    Returns:
        Python dict representing the HTML document tree

    Raises:
        HTMLParseError: If parsing fails
    """
    try:
        soup = BeautifulSoup(content, "html.parser")

        # Find the root element (usually <html>, but could be first tag)
        root_element = None
        for element in soup.children:
            if isinstance(element, Tag):
                root_element = element
                break

        if root_element is None:
            raise HTMLParseError("No HTML elements found")

        return _tag_to_dict(root_element)
    except Exception as e:
        if isinstance(e, HTMLParseError):
            raise
        raise HTMLParseError(f"Failed to parse HTML: {e}") from e


def _tag_to_dict(tag: Tag) -> Dict[str, Any]:
    """
    Convert BeautifulSoup Tag to dict structure.

    Args:
        tag: BeautifulSoup Tag to convert

    Returns:
        Dict representation of the tag
    """
    result = {
        "type": tag.name,
    }

    # Add attributes
    if tag.attrs:
        # Handle attributes that might have lists as values (like 'class')
        for key, value in tag.attrs.items():
            if isinstance(value, list):
                result[key] = " ".join(value)
            else:
                result[key] = value

    # Process children and text content
    children = []
    text_content_parts = []

    for child in tag.children:
        if isinstance(child, Tag):
            # Child element
            children.append(_tag_to_dict(child))
        elif isinstance(child, NavigableString):
            # Text content
            text = str(child).strip()
            if text:
                text_content_parts.append(text)
                children.append(text)

    # Set children if we have any
    if children:
        result["children"] = children

    # Set text field for backward compatibility (combined text only)
    if text_content_parts:
        combined_text = " ".join(text_content_parts).strip()
        if combined_text:
            result["text"] = combined_text

    return result
