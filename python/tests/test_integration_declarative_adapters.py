"""
Integration tests for declarative adapters.

Tests that JSON definition files properly adapt real-world data
to treeviz Node structures.
"""

import json
import pytest
from pathlib import Path
from dataclasses import asdict

from treeviz.adapters import adapt_node
from treeviz.definitions import Lib


class TestDeclarativeAdapterIntegration:
    """Integration tests for declarative adapter system."""

    @pytest.mark.parametrize(
        "format_name,data_file,expected_root_type,min_node_types,expected_content",
        [
            (
                "mdast",
                "comprehensive_example.json",
                "root",
                {"root", "heading", "paragraph", "text", "list", "listItem"},
                ["MDAST Comprehensive Example", "bold text"],
            ),
            (
                "unist",
                "comprehensive_example.json",
                "root",
                {"root", "element", "text"},
                ["section", "article", "h1", "p"],
            ),
        ],
    )
    def test_format_data_integration(
        self,
        format_name,
        data_file,
        expected_root_type,
        min_node_types,
        expected_content,
    ):
        """Test comprehensive format parsing and adapter application."""
        # Load test data
        test_data_path = (
            Path(__file__).parent / "test_data" / format_name / data_file
        )
        with open(test_data_path) as f:
            test_data = json.load(f)

        # Get format definition
        format_def = asdict(Lib.get(format_name))

        # Adapt the data
        result = adapt_node(test_data, format_def)

        # Basic structure validation
        assert result.type == expected_root_type
        assert len(result.children) > 0

        # Check that we have expected node types
        node_types = self._collect_node_types(result)
        found_types = min_node_types & node_types
        assert (
            len(found_types) >= len(min_node_types) - 1
        ), f"Missing node types. Found: {node_types}"

        # Check that expected content is preserved
        all_nodes = self._flatten_nodes(result)
        all_labels = [n.label for n in all_nodes if n.label]

        for expected_text in expected_content:
            assert any(
                expected_text in label for label in all_labels
            ), f"Expected content '{expected_text}' not found in labels: {all_labels[:5]}..."

    def test_mdast_node_hierarchy_preservation(self):
        """Test that MDAST node hierarchy is preserved correctly."""
        test_data_path = (
            Path(__file__).parent
            / "test_data"
            / "mdast"
            / "comprehensive_example.json"
        )
        with open(test_data_path) as f:
            mdast_data = json.load(f)

        mdast_def = asdict(Lib.get("mdast"))
        result = adapt_node(mdast_data, mdast_def)

        # Find a list node and verify its structure
        list_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "list"
        ]
        assert len(list_nodes) >= 1, "Should have at least 1 list"

        # Check that list has listItem children
        list_node = list_nodes[0]
        list_item_children = [
            c for c in list_node.children if c.type == "listItem"
        ]
        assert len(list_item_children) >= 1, "List should have at least 1 item"

        # Check hierarchical structure preservation
        first_item = list_item_children[0]
        assert len(first_item.children) >= 1, "List item should have children"

    def _collect_node_types(self, node):
        """Collect all node types in the tree."""
        types = {node.type}
        for child in node.children:
            types.update(self._collect_node_types(child))
        return types

    def _flatten_nodes(self, node):
        """Flatten tree into list of all nodes."""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._flatten_nodes(child))
        return nodes
