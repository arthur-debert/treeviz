"""
Test fixtures and utilities for treeviz tests.

This module provides reusable fixtures and helper functions for loading test data,
creating test objects, and performing common assertions.
"""

import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

from treeviz.model import Node


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
    test_data_dir = Path(__file__).parent.parent / "test_data"
    file_path = test_data_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assert_node(
    node: Node,
    *,
    label: Optional[str] = None,
    type: Optional[str] = None,
    icon: Optional[str] = None,
    content_lines: Optional[int] = None,
    source_location: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    children: Optional[List[Node]] = None,
    children_count: Optional[int] = None
) -> None:
    """
    Custom assertion for Node objects with detailed error messages.
    
    Args:
        node: The Node object to check
        label: Expected label value
        type: Expected type value
        icon: Expected icon value
        content_lines: Expected content_lines value
        source_location: Expected source_location dict
        metadata: Expected metadata dict
        children: Expected list of child nodes (exact match)
        children_count: Expected number of children (count only)
        
    Example:
        >>> assert_node(node, label="Test", type="container", children_count=2)
    """
    if label is not None:
        assert node.label == label, f"Expected label '{label}', got '{node.label}'"
    
    if type is not None:
        assert node.type == type, f"Expected type '{type}', got '{node.type}'"
    
    if icon is not None:
        assert node.icon == icon, f"Expected icon '{icon}', got '{node.icon}'"
    
    if content_lines is not None:
        assert node.content_lines == content_lines, f"Expected content_lines {content_lines}, got {node.content_lines}"
    
    if source_location is not None:
        assert node.source_location == source_location, f"Expected source_location {source_location}, got {node.source_location}"
    
    if metadata is not None:
        assert node.metadata == metadata, f"Expected metadata {metadata}, got {node.metadata}"
    
    if children is not None:
        assert node.children == children, f"Expected children {children}, got {node.children}"
    
    if children_count is not None:
        actual_count = len(node.children) if node.children else 0
        assert actual_count == children_count, f"Expected {children_count} children, got {actual_count}"


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