"""
Tests for the 3viz data model.
"""

from treeviz.model import Node


def test_node_creation():
    """Test creating a basic Node."""
    node = Node(label="Test Node")

    assert node.label == "Test Node"
    assert node.type is None
    assert node.icon is None
    assert node.content_lines == 1
    assert node.source_location is None
    assert node.metadata == {}
    assert node.children == []


def test_node_with_all_fields():
    """Test creating a Node with all fields populated."""
    child = Node(label="Child")

    node = Node(
        label="Parent Node",
        type="container",
        icon="⧉",
        content_lines=5,
        source_location={"line": 10, "column": 5},
        metadata={"key": "value"},
        children=[child],
    )

    assert node.label == "Parent Node"
    assert node.type == "container"
    assert node.icon == "⧉"
    assert node.content_lines == 5
    assert node.source_location == {"line": 10, "column": 5}
    assert node.metadata == {"key": "value"}
    assert len(node.children) == 1
    assert node.children[0] == child


def test_node_tree_structure():
    """Test creating a tree structure with Node."""
    leaf1 = Node(label="Leaf 1", type="text")
    leaf2 = Node(label="Leaf 2", type="text")

    branch = Node(label="Branch", type="container", children=[leaf1, leaf2])

    root = Node(label="Root", type="document", children=[branch])

    assert len(root.children) == 1
    assert root.children[0] == branch
    assert len(branch.children) == 2
    assert branch.children[0] == leaf1
    assert branch.children[1] == leaf2


def test_node_metadata_extensibility():
    """Test that metadata can store arbitrary data."""
    node = Node(
        label="Test",
        metadata={
            "custom_field": "value",
            "nested": {"inner": "data"},
            "list_data": [1, 2, 3],
            "boolean": True,
        },
    )

    assert node.metadata["custom_field"] == "value"
    assert node.metadata["nested"]["inner"] == "data"
    assert node.metadata["list_data"] == [1, 2, 3]
    assert node.metadata["boolean"] is True
