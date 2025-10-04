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

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def assert_node_properties(
    node: Node,
    *,
    label: Optional[str] = None,
    type: Optional[str] = None,
    icon: Optional[str] = None,
    content_lines: Optional[int] = None,
    source_location: Optional[Dict] = None,
    extra: Optional[Dict] = None,
    children: Optional[List[Node]] = None,
    children_count: Optional[int] = None,
) -> None:
    """
    DEPRECATED: Use the assert_node fixture from conftest.py instead.

    Custom assertion for Node objects with detailed error messages.
    This function is kept for backward compatibility but the pytest fixture
    approach in conftest.py is preferred.

    New usage:
        def test_something(assert_node):
            assert_node(node).has_label("test").has_type("container")

    Old usage (still works):
        assert_node_properties(node, label="test", type="container")
    """
    if label is not None:
        assert (
            node.label == label
        ), f"Expected label '{label}', got '{node.label}'"

    if type is not None:
        assert node.type == type, f"Expected type '{type}', got '{node.type}'"

    if icon is not None:
        assert node.icon == icon, f"Expected icon '{icon}', got '{node.icon}'"

    if content_lines is not None:
        assert (
            node.content_lines == content_lines
        ), f"Expected content_lines {content_lines}, got {node.content_lines}"

    if source_location is not None:
        assert (
            node.source_location == source_location
        ), f"Expected source_location {source_location}, got {node.source_location}"

    if extra is not None:
        assert node.extra == extra, f"Expected extra {extra}, got {node.extra}"

    if children is not None:
        assert (
            node.children == children
        ), f"Expected children {children}, got {node.children}"

    if children_count is not None:
        actual_count = len(node.children) if node.children else 0
        assert (
            actual_count == children_count
        ), f"Expected {children_count} children, got {actual_count}"


# Backward compatibility alias
assert_node = assert_node_properties


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
    child = Node(type="text", label="Child text", content_lines=0)

    return Node(
        type="container",
        label="Parent Node",
        icon="⧉",
        content_lines=5,
        source_location={"line": 10, "column": 5},
        extra={"key": "value"},
        children=[child],
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
                type="paragraph", label="This is a paragraph.", content_lines=0
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
