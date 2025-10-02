"""
Tests for the MdastAdapter.
"""

from treeviz.adapters.mdast import MdastAdapter
from treeviz.model import Node


def test_adapt_simple_mdast_tree(simple_mdast_tree, assert_node):
    """
    Test adapting a simple mdast tree.
    """
    # Adapt the mdast tree to the 3viz data model
    adapter = MdastAdapter()
    node_tree = adapter.adapt(simple_mdast_tree)

    # Root node assertions
    assert isinstance(node_tree, Node)
    assert_node(node_tree).has_type("root").has_children_count(3)

    # Check children
    heading_node = node_tree.children[0]
    assert_node(heading_node).has_type("heading")
    assert heading_node.metadata["depth"] == 1
    assert "Hello, world!" in heading_node.label

    paragraph_node = node_tree.children[1]
    assert_node(paragraph_node).has_type("paragraph")
    assert "This is a paragraph." in paragraph_node.label

    list_node = node_tree.children[2]
    assert_node(list_node).has_type("list").has_children_count(2)

    item1_node = list_node.children[0]
    assert_node(item1_node).has_type("listItem")
    assert "Item 1" in item1_node.label
