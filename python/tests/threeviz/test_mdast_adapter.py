"""
Tests for the MdastAdapter.
"""

import pytest

from treeviz.adapters.mdast import MdastAdapter
from treeviz.model import Node


@pytest.fixture
def simple_mdast_tree():
    """
    A simple mdast tree for testing.
    """
    return {
        "type": "root",
        "children": [
            {
                "type": "heading",
                "depth": 1,
                "children": [{"type": "text", "value": "Hello, world!"}],
            },
            {
                "type": "paragraph",
                "children": [{"type": "text", "value": "This is a paragraph."}],
            },
            {
                "type": "list",
                "ordered": False,
                "children": [
                    {
                        "type": "listItem",
                        "children": [
                            {
                                "type": "paragraph",
                                "children": [
                                    {"type": "text", "value": "Item 1"}
                                ],
                            }
                        ],
                    },
                    {
                        "type": "listItem",
                        "children": [
                            {
                                "type": "paragraph",
                                "children": [
                                    {"type": "text", "value": "Item 2"}
                                ],
                            }
                        ],
                    },
                ],
            },
        ],
    }


def test_adapt_simple_mdast_tree(simple_mdast_tree):
    """
    Test adapting a simple mdast tree.
    """
    # Adapt the mdast tree to the 3viz data model
    adapter = MdastAdapter()
    node_tree = adapter.adapt(simple_mdast_tree)

    # Assertions
    assert isinstance(node_tree, Node)
    assert node_tree.type == "root"
    assert len(node_tree.children) == 3

    heading_node = node_tree.children[0]
    assert heading_node.type == "heading"
    assert heading_node.metadata["depth"] == 1
    assert "Hello, world!" in heading_node.label

    paragraph_node = node_tree.children[1]
    assert paragraph_node.type == "paragraph"
    assert "This is a paragraph." in paragraph_node.label

    list_node = node_tree.children[2]
    assert list_node.type == "list"
    assert len(list_node.children) == 2

    item1_node = list_node.children[0]
    assert item1_node.type == "listItem"
    assert "Item 1" in item1_node.label
