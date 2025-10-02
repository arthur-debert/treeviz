"""
Tests for the UnistAdapter.
"""

import pytest

from treeviz.adapters.unist import UnistAdapter
from treeviz.model import Node


def test_adapt_simple_unist_tree(simple_unist_tree, assert_node):
    """
    Test adapting a simple unist tree.
    """
    # Adapt the unist tree to the 3viz data model
    adapter = UnistAdapter()
    node_tree = adapter.adapt(simple_unist_tree)

    # Root node assertions
    assert isinstance(node_tree, Node)
    assert_node(node_tree).has_type("root").has_children_count(1)

    # Check paragraph
    paragraph_node = node_tree.children[0]
    assert_node(paragraph_node).has_type("paragraph").has_children_count(1)
    assert "Hello, world!" in paragraph_node.label

    # Check text node
    text_node = paragraph_node.children[0]
    assert_node(text_node).has_type("text").has_label("Hello, world!")
