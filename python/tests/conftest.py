"""
Pytest configuration and custom assertions for treeviz tests.

This file provides pytest fixtures and custom assertion methods that are available
to all test files automatically.
"""

import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

from treeviz.model import Node


class NodeAssertion:
    """Custom assertion class for Node objects with fluent interface."""
    
    def __init__(self, node: Node):
        self.node = node
        
    def has_label(self, expected: str) -> 'NodeAssertion':
        """Assert node has expected label."""
        assert self.node.label == expected, f"Expected label '{expected}', got '{self.node.label}'"
        return self
        
    def has_type(self, expected: str) -> 'NodeAssertion':
        """Assert node has expected type."""
        assert self.node.type == expected, f"Expected type '{expected}', got '{self.node.type}'"
        return self
        
    def has_icon(self, expected: str) -> 'NodeAssertion':
        """Assert node has expected icon."""
        assert self.node.icon == expected, f"Expected icon '{expected}', got '{self.node.icon}'"
        return self
        
    def has_content_lines(self, expected: int) -> 'NodeAssertion':
        """Assert node has expected content lines."""
        assert self.node.content_lines == expected, f"Expected content_lines {expected}, got {self.node.content_lines}"
        return self
        
    def has_source_location(self, expected: Dict) -> 'NodeAssertion':
        """Assert node has expected source location."""
        assert self.node.source_location == expected, f"Expected source_location {expected}, got {self.node.source_location}"
        return self
        
    def has_metadata(self, expected: Dict) -> 'NodeAssertion':
        """Assert node has expected metadata."""
        assert self.node.metadata == expected, f"Expected metadata {expected}, got {self.node.metadata}"
        return self
        
    def has_children_count(self, expected: int) -> 'NodeAssertion':
        """Assert node has expected number of children."""
        actual_count = len(self.node.children) if self.node.children else 0
        assert actual_count == expected, f"Expected {expected} children, got {actual_count}"
        return self
        
    def has_children(self, expected: List[Node]) -> 'NodeAssertion':
        """Assert node has exactly these children."""
        assert self.node.children == expected, f"Expected children {expected}, got {self.node.children}"
        return self


@pytest.fixture
def assert_node():
    """
    Pytest fixture that returns a function for asserting Node properties.
    
    Returns a function that takes a Node and returns a NodeAssertion object
    for fluent-style assertions.
    
    Usage:
        def test_node(assert_node):
            node = Node(type="test", label="Test Node")
            assert_node(node).has_type("test").has_label("Test Node")
    """
    def _assert_node(node: Node) -> NodeAssertion:
        return NodeAssertion(node)
    return _assert_node


def load_test_data(filename: str) -> Any:
    """
    Load test data from a JSON file in the test_data directory.
    
    Args:
        filename: Path to the JSON file relative to tests/test_data/
        
    Returns:
        The parsed JSON data
        
    Example:
        >>> data = load_test_data("mdast/simple_tree.json")
    """
    test_data_dir = Path(__file__).parent / "test_data"
    file_path = test_data_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Common test fixtures

@pytest.fixture
def simple_mdast_tree():
    """Load simple MDAST tree test data."""
    return load_test_data("mdast/simple_tree.json")


@pytest.fixture  
def simple_unist_tree():
    """Load simple UNIST tree test data."""
    return load_test_data("unist/simple_tree.json")


@pytest.fixture
def sample_node():
    """Create a sample Node for testing."""
    child = Node(
        type="text",
        label="Child text",
        content_lines=0
    )
    
    return Node(
        type="container",
        label="Parent Node",
        icon="⧉",
        content_lines=5,
        source_location={"line": 10, "column": 5},
        metadata={"key": "value"},
        children=[child]
    )


@pytest.fixture
def sample_node_tree():
    """Create a sample node tree for renderer testing."""
    return Node(
        type="document",
        label="Document",
        content_lines=2,
        children=[
            Node(
                type="paragraph", 
                label="This is a paragraph.", 
                content_lines=0
            ),
            Node(
                type="list",
                label="List",
                content_lines=2,
                children=[
                    Node(type="listItem", label="Item 1", content_lines=0),
                    Node(type="listItem", label="Item 2", content_lines=0),
                ],
            ),
        ],
    )