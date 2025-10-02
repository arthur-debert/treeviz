"""
Tests for the UnistAdapter.
"""

import pytest

from treeviz.adapters.unist import UnistAdapter
from treeviz.model import Node
from ..fixtures import simple_unist_tree, assert_node


def test_adapt_simple_unist_tree(simple_unist_tree):
    """
    Test adapting a simple unist tree.
    """
    # Adapt the unist tree to the 3viz data model
    adapter = UnistAdapter()
    node_tree = adapter.adapt(simple_unist_tree)

    # Assertions
    assert isinstance(node_tree, Node)
    assert node_tree.type == "root"
    assert len(node_tree.children) == 1

    paragraph_node = node_tree.children[0]
    assert paragraph_node.type == "paragraph"
    assert len(paragraph_node.children) == 1
    assert "Hello, world!" in paragraph_node.label

    text_node = paragraph_node.children[0]
    assert text_node.type == "text"
    assert text_node.label == "Hello, world!"
