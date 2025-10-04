import pytest
from pathlib import Path
from dataclasses import asdict

from treeviz.adapters import adapt_node
from treeviz.definitions import AdapterLib
from treeviz.formats.parser import parse_document

class TestAsciidocAdapter:
    """Tests for the AsciiDoc declarative adapter."""

    def _collect_node_types(self, node):
        """Helper to collect all node types in the tree for assertion."""
        types = {node.type}
        for child in node.children:
            types.update(self._collect_node_types(child))
        return types

    def _flatten_nodes(self, node):
        """Helper to flatten the tree into a list of nodes."""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._flatten_nodes(child))
        return nodes

    def test_asciidoc_adapter_on_article(self):
        """
        Tests the built-in 'asciidoc' adapter against a comprehensive
        DocBook XML file to ensure it's parsed correctly.
        """
        # 1. Load test data from article.xml
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")

        # 2. Get the 'asciidoc' adapter definition from the library
        adapter_def = asdict(AdapterLib.get("asciidoc"))

        # 3. Adapt the source node into a 3viz Node tree
        result = adapt_node(source_node, adapter_def)

        # 4. Assertions
        assert result.type == "article", "Root node type should be 'article'"
        assert "The Article Title" in result.label, "Article title was not extracted correctly"
        assert len(result.children) > 0, "Article should have children"

        # Check that key node types are present in the tree
        node_types = self._collect_node_types(result)
        expected_types = {"article", "section", "title", "simpara", "table", "row", "entry"}
        assert expected_types.issubset(node_types), f"Missing expected node types. Found: {node_types}"

        # Check for specific content in labels to ensure correct parsing and transformation
        all_labels = [n.label for n in self._flatten_nodes(result) if n.label]

        expected_content = [
            "§ The First Section",
            "Sub-section with Anchor",
            "Example Appendix",
            "Example Bibliography",
            "Example Glossary"
        ]

        for expected_text in expected_content:
            assert any(
                expected_text in label for label in all_labels
            ), f"Expected content '{expected_text}' not found in labels"