"""
Tests for the 3viz data model.
"""

from treeviz.model import Node


def test_node_creation(assert_node):
    """Test creating a basic Node."""
    node = Node(label="Test Node")

    # Using the new fluent assertion style
    assert_node(node).has_label("Test Node").has_content_lines(1).has_children_count(0)
    
    # Check None/empty values
    assert node.type is None
    assert node.icon is None
    assert node.source_location is None
    assert node.metadata == {}


def test_node_with_all_fields(assert_node):
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

    # Using the new fluent assertion style
    (assert_node(node)
     .has_label("Parent Node")
     .has_type("container")
     .has_icon("⧉")
     .has_content_lines(5)
     .has_source_location({"line": 10, "column": 5})
     .has_metadata({"key": "value"})
     .has_children_count(1))
    
    # Check the child directly
    assert node.children[0] == child


def test_node_tree_structure(assert_node):
    """Test creating a tree structure with Node."""
    leaf1 = Node(label="Leaf 1", type="text")
    leaf2 = Node(label="Leaf 2", type="text")

    branch = Node(label="Branch", type="container", children=[leaf1, leaf2])

    root = Node(label="Root", type="document", children=[branch])

    # Using fluent assertions for structure validation
    assert_node(root).has_children_count(1)
    assert_node(branch).has_children_count(2)
    
    # Check direct relationships
    assert root.children[0] == branch
    assert branch.children[0] == leaf1
    assert branch.children[1] == leaf2


def test_node_metadata_extensibility(assert_node):
    """Test that metadata can store arbitrary data."""
    metadata = {
        "custom_field": "value",
        "nested": {"inner": "data"},
        "list_data": [1, 2, 3],
        "boolean": True,
    }
    
    node = Node(label="Test", metadata=metadata)

    # Use fluent assertion for metadata check
    assert_node(node).has_metadata(metadata)
    
    # Test individual metadata access
    assert node.metadata["custom_field"] == "value"
    assert node.metadata["nested"]["inner"] == "data"
    assert node.metadata["list_data"] == [1, 2, 3]
    assert node.metadata["boolean"] is True
