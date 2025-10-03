"""
XML format parser using xml.etree.ElementTree.

This module provides robust XML parsing using Python's built-in XML parser,
which is secure and handles XML declarations, namespaces, and other XML features.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any


class XMLParseError(Exception):
    """Exception raised when XML parsing fails."""

    pass


def parse_xml(content: str) -> Dict[str, Any]:
    """
    Parse XML content into Python dict structure.

    Args:
        content: XML document content

    Returns:
        Python dict representing the XML document tree

    Raises:
        XMLParseError: If parsing fails
    """
    try:
        root = ET.fromstring(content)
        return _element_to_dict(root)
    except ET.ParseError as e:
        raise XMLParseError(f"Failed to parse XML: {e}") from e


def _element_to_dict(element: ET.Element) -> Dict[str, Any]:
    """
    Convert XML Element to dict structure.

    Args:
        element: XML Element to convert

    Returns:
        Dict representation of the element
    """
    result = {
        "type": _get_tag_name(element.tag),
    }

    # Add attributes
    if element.attrib:
        result.update(element.attrib)

    # Process children and text content
    children = []
    text_content_parts = []

    # Add text content before first child
    if element.text and element.text.strip():
        text_content_parts.append(element.text.strip())
        children.append(element.text.strip())

    # Process child elements
    for child in element:
        children.append(_element_to_dict(child))

        # Add tail text after this child (text between child tags)
        if child.tail and child.tail.strip():
            text_content_parts.append(child.tail.strip())
            children.append(child.tail.strip())

    # Set children if we have any
    if children:
        result["children"] = children

    # Set text field for backward compatibility (combined text only)
    if text_content_parts:
        combined_text = " ".join(text_content_parts).strip()
        if combined_text:
            result["text"] = combined_text

    return result


def _get_tag_name(tag: str) -> str:
    """
    Extract tag name from potentially namespaced tag.

    Args:
        tag: Tag name (may include namespace)

    Returns:
        Clean tag name without namespace prefix
    """
    if "}" in tag:
        # Remove namespace: {namespace}tagname -> tagname
        return tag.split("}", 1)[1]
    return tag
