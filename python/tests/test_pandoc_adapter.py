"""
Integration tests for the Pandoc python-based adapter.
"""

from treeviz.adapters import adapt_node
from treeviz.data.pandoc import definition as pandoc_def
from .conftest import load_test_data


def _flatten_nodes(node):
    """Flatten tree into a list of all nodes."""
    nodes = [node]
    if node and node.children:
        for child in node.children:
            nodes.extend(_flatten_nodes(child))
    return nodes


def _get_test_data():
    """
    Loads the Pandoc test data and applies a hack to make the root
    node's structure consistent with the rest of the tree.
    """
    original_data = load_test_data("pandoc/pandoc_test.json")

    # The hack: wrap the original data in a new root object that has a 't' key.
    return {
        "t": "Pandoc",
        "blocks": original_data["blocks"],
        "meta": original_data["meta"],
        "pandoc-api-version": original_data["pandoc-api-version"],
    }


def test_pandoc_adapter_integration():
    """Test that the pandoc adapter correctly transforms a test AST."""
    test_data = _get_test_data()

    # Adapt the data using the pandoc adapter
    result = adapt_node(test_data, pandoc_def)

    # Verify the root node
    assert result is not None, "Adaptation should not result in None"
    assert result.type == "Pandoc"
    assert result.label == "Pandoc Document"
    assert len(result.children) > 0

    # Flatten the tree to inspect all nodes
    all_nodes = _flatten_nodes(result)
    node_types = {n.type for n in all_nodes}

    # Check for expected node types
    expected_types = {"Pandoc", "Header", "Para", "BulletList", "OrderedList", "ListItem", "CodeBlock"}
    assert expected_types.issubset(node_types)

    # Check for specific content
    labels = {n.label for n in all_nodes}
    assert "H1: This is a test document" in labels
    assert "H2: Lists" in labels
    assert any("Item 1" in label for label in labels)


def test_pandoc_list_item_creation():
    """Test that synthetic 'ListItem' nodes are created correctly."""
    test_data = _get_test_data()

    # Adapt the data
    result = adapt_node(test_data, pandoc_def)
    assert result is not None

    # Find a bullet list and check its children
    all_nodes = _flatten_nodes(result)
    bullet_lists = [n for n in all_nodes if n.type == "BulletList"]
    assert len(bullet_lists) > 0, "No BulletList nodes found"

    list_item_children = [child for child in bullet_lists[0].children if child.type == "ListItem"]
    assert len(list_item_children) > 0, "No ListItem children found in BulletList"
    assert "Item 1" in list_item_children[0].label
    assert "Item 2" in list_item_children[1].label