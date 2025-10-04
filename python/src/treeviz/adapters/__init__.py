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

from .core import adapt_node, adapt_tree
from .utils import exit_on_error, load_adapter
from .extraction import (
    extract_attribute,
    extract_by_path,
    apply_transformation,
    filter_collection,
)

__all__ = [
    "adapt_node",
    "adapt_tree",
    "exit_on_error",
    "load_adapter",
    "extract_attribute",
    "extract_by_path",
    "apply_transformation",
    "filter_collection",
]
