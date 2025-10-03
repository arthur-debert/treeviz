"""
Test declarative adapters with comprehensive real-world examples.

This module tests that the JSON definition files properly adapt
MDAST and UNIST examples to treeviz Node structures.
"""

import json
from pathlib import Path

from treeviz.adapter import adapt_node
from treeviz.definitions import load_format_def


class TestDeclarativeAdapters:
    """Test that declarative adapters work with comprehensive examples."""

    def test_mdast_comprehensive_example(self):
        """Test MDAST definition with comprehensive example."""
        # Load test data
        test_data_path = (
            Path(__file__).parent
            / "test_data"
            / "mdast"
            / "comprehensive_example.json"
        )
        with open(test_data_path) as f:
            mdast_data = json.load(f)

        # Get MDAST definition
        mdast_def = load_format_def("mdast").to_dict()

        # Adapt the data
        result = adapt_node(mdast_data, mdast_def)

        # Basic structure validation
        assert result.type == "root"
        assert len(result.children) > 0

        # Check that we have various node types
        node_types = self._collect_node_types(result)
        expected_types = {
            "root",
            "heading",
            "paragraph",
            "text",
            "list",
            "listItem",
            "blockquote",
            "code",
        }

        # Should have most of the expected types
        assert (
            len(expected_types & node_types) >= 6
        ), f"Missing node types. Found: {node_types}"

        # Validate specific nodes
        heading_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "heading"
        ]
        assert len(heading_nodes) >= 3, "Should have at least 3 headings"

        paragraph_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "paragraph"
        ]
        assert len(paragraph_nodes) >= 3, "Should have at least 3 paragraphs"

        # Check that text content is preserved
        text_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "text"
        ]
        text_values = [n.label for n in text_nodes]
        assert any(
            "MDAST Comprehensive Example" in text for text in text_values
        )
        assert any("bold text" in text for text in text_values)

    def test_unist_comprehensive_example(self):
        """Test UNIST definition with comprehensive example."""
        # Load test data
        test_data_path = (
            Path(__file__).parent
            / "test_data"
            / "unist"
            / "comprehensive_example.json"
        )
        with open(test_data_path) as f:
            unist_data = json.load(f)

        # Get UNIST definition
        unist_def = load_format_def("unist").to_dict()

        # Adapt the data
        result = adapt_node(unist_data, unist_def)

        # Basic structure validation
        assert result.type == "root"
        assert len(result.children) > 0

        # Check that we have various node types
        node_types = self._collect_node_types(result)
        expected_types = {"root", "element", "text", "comment"}

        # Should have most of the expected types
        assert (
            len(expected_types & node_types) >= 3
        ), f"Missing node types. Found: {node_types}"

        # Validate specific nodes
        element_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "element"
        ]
        assert len(element_nodes) >= 5, "Should have at least 5 elements"

        text_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "text"
        ]
        assert len(text_nodes) >= 3, "Should have at least 3 text nodes"

        # Check that element labels use tagName (due to type_overrides)
        element_labels = [n.label for n in element_nodes]
        expected_tags = {"section", "article", "h1", "p", "ul", "li"}
        found_tags = set(element_labels)
        assert (
            len(expected_tags & found_tags) >= 4
        ), f"Missing expected tags. Found: {found_tags}"

    def test_mdast_node_hierarchy(self):
        """Test that MDAST node hierarchy is preserved."""
        test_data_path = (
            Path(__file__).parent
            / "test_data"
            / "mdast"
            / "comprehensive_example.json"
        )
        with open(test_data_path) as f:
            mdast_data = json.load(f)

        mdast_def = load_format_def("mdast").to_dict()
        result = adapt_node(mdast_data, mdast_def)

        # Find a list node and verify its structure
        list_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "list"
        ]
        assert len(list_nodes) >= 2, "Should have at least 2 lists"

        # Check that list has listItem children
        ordered_list = list_nodes[0]  # First list should be ordered
        list_item_children = [
            c for c in ordered_list.children if c.type == "listItem"
        ]
        assert (
            len(list_item_children) >= 2
        ), "Ordered list should have at least 2 items"

        # Check that listItems have paragraph children
        first_item = list_item_children[0]
        paragraph_children = [
            c for c in first_item.children if c.type == "paragraph"
        ]
        assert (
            len(paragraph_children) >= 1
        ), "List item should have paragraph child"

    def test_unist_element_attributes(self):
        """Test that UNIST element attributes are handled correctly."""
        test_data_path = (
            Path(__file__).parent
            / "test_data"
            / "unist"
            / "comprehensive_example.json"
        )
        with open(test_data_path) as f:
            unist_data = json.load(f)

        unist_def = load_format_def("unist").to_dict()
        result = adapt_node(unist_data, unist_def)

        # Find elements and check their labels use tagName
        element_nodes = [
            n for n in self._flatten_nodes(result) if n.type == "element"
        ]

        # Should have elements with various tag names
        tag_names = set(n.label for n in element_nodes)
        expected_tags = {"section", "article", "h1", "p"}
        assert (
            len(expected_tags & tag_names) >= 3
        ), f"Missing expected tag names. Found: {tag_names}"

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
