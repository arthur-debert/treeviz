"""
Declarative Converter Engine for 3viz

This module provides a declarative way to adapt any tree structure to the 3viz
Node format. Instead of writing custom adapter code, users can specify how to
extract information from their AST using simple attribute mappings.

Example usage:
    def_ = {
        "label": "name",
        "type": "node_type", 
        "children": "child_nodes",
        "icons": {
            "paragraph": "¶",
            "list": "☰"
        }
    }
    
    node = adapt_node(my_ast_node, def_)
"""

import sys
from typing import Any, Dict, Optional, Callable

from .model import Node
from .advanced_extraction import extract_attribute
from .definitions.schema import Definition


def adapt_node(source_node: Any, def_: Dict[str, Any]) -> Optional[Node]:
    """
    Adapt a source AST node to a 3viz Node.

    Args:
        source_node: The source AST node to adapt
        def_: Dictionary containing attribute mappings and icon mappings

    Returns:
        3viz Node or None if node should be ignored

    Raises:
        Standard Python exceptions: TypeError, KeyError, ValueError, etc. with descriptive messages
    """
    # Parse and validate using dataclass
    definition = Definition.from_dict(def_)

    # Check if this node type should be ignored
    node_type = extract_attribute(source_node, definition.type)
    if node_type and node_type in definition.ignore_types:
        return None

    # Get the effective extraction mappings for this node type
    effective_label = definition.label
    effective_type = definition.type
    effective_children = definition.children
    effective_icon = definition.icon
    effective_content_lines = definition.content_lines
    effective_source_location = definition.source_location
    effective_metadata = definition.metadata

    # Apply type-specific overrides if they exist
    if node_type and node_type in definition.type_overrides:
        overrides = definition.type_overrides[node_type]
        effective_label = overrides.get("label", effective_label)
        effective_type = overrides.get("type", effective_type)
        effective_children = overrides.get("children", effective_children)
        effective_icon = overrides.get("icon", effective_icon)
        effective_content_lines = overrides.get(
            "content_lines", effective_content_lines
        )
        effective_source_location = overrides.get(
            "source_location", effective_source_location
        )
        effective_metadata = overrides.get("metadata", effective_metadata)

    # Extract basic attributes using advanced extractor
    label = extract_attribute(source_node, effective_label)
    if label is None:
        label = str(node_type) if node_type else "Unknown"

    # Extract optional attributes using advanced extractor
    icon = extract_attribute(source_node, effective_icon)
    content_lines = extract_attribute(source_node, effective_content_lines)
    if not isinstance(content_lines, int):
        content_lines = 1
    
    source_location = extract_attribute(source_node, effective_source_location)
    
    # Extract metadata using advanced extractor
    extracted_metadata = extract_attribute(source_node, effective_metadata)
    metadata = extracted_metadata if extracted_metadata is not None else {}

    # Apply icon mapping if no explicit icon
    if not icon and node_type and node_type in definition.icons:
        icon = definition.icons[node_type]

    # Extract children using advanced extractor (supports filtering)
    children = []
    children_source = extract_attribute(source_node, effective_children)
    if children_source:
        if not isinstance(children_source, list):
            raise TypeError(
                f"Children attribute must return a list, got {type(children_source).__name__}. "
                f"Check your 'children' attribute mapping in the definition."
            )

        for child in children_source:
            child_node = adapt_node(child, def_)
            if child_node is not None:  # Skip ignored nodes
                children.append(child_node)

    return Node(
        label=str(label),
        type=node_type,
        icon=icon,
        content_lines=content_lines,
        source_location=source_location,
        metadata=metadata,
        children=children,
    )


def adapt_tree(source_tree: Any, def_: Dict[str, Any]) -> Node:
    """
    Convenience function to adapt a tree with definition.

    Args:
        source_tree: The root of the source AST
        def_: Declarative converter definition

    Returns:
        Converted 3viz Node tree

    Raises:
        ValueError: If root node is ignored
        Standard Python exceptions: From adapt_node if other errors occur
    """
    result = adapt_node(source_tree, def_)

    if result is None:
        raise ValueError(
            "Root node was ignored - check ignore_types definition. "
            "The root node type may be in the ignore_types list."
        )

    return result


def exit_on_error(func: Callable) -> Callable:
    """
    Decorator to exit with status 1 on any exception.

    This implements the "fail fast" principle - any error
    should immediately exit the program with a clear error message.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
