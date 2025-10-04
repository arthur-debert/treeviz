"""
Comprehensive tests for the AsciiDoc declarative adapter.

This test suite validates the adapter's ability to handle DocBook XML
generated from AsciiDoc documents, including edge cases and error resilience.
"""

from pathlib import Path
from dataclasses import asdict

from treeviz.adapters import adapt_node
from treeviz.definitions import AdapterLib
from treeviz.formats.parser import parse_document


class TestAsciidocAdapter:
    """Tests for the AsciiDoc declarative adapter using real DocBook XML."""

    def _collect_node_types(self, node):
        """Recursively collect all node types in the tree."""
        types = {node.type}
        for child in node.children:
            types.update(self._collect_node_types(child))
        return types

    def _flatten_nodes(self, node):
        """Flatten the tree into a list of nodes for content analysis."""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._flatten_nodes(child))
        return nodes

    def _find_nodes_by_type(self, node, node_type):
        """Find all nodes of a specific type in the tree."""
        matches = []
        if node.type == node_type:
            matches.append(node)
        for child in node.children:
            matches.extend(self._find_nodes_by_type(child, node_type))
        return matches

    def test_asciidoc_adapter_loads_correctly(self):
        """Test that the YAML AsciiDoc adapter loads correctly."""
        adapter_def = AdapterLib.get("asciidoc")
        assert adapter_def is not None, "AsciiDoc adapter should load"
        assert (
            adapter_def.type == "type"
        ), "Default type extraction should be 'type'"
        assert (
            adapter_def.children == "children"
        ), "Default children extraction should be 'children'"
        assert len(adapter_def.icons) > 0, "Should have icon mappings"

    def test_asciidoc_adapter_on_comprehensive_article(self):
        """
        Test the AsciiDoc adapter against a comprehensive DocBook XML file
        to ensure robust parsing and content extraction.
        """
        # Load test data from article.xml
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")

        # Get the asciidoc adapter definition
        adapter_def = asdict(AdapterLib.get("asciidoc"))

        # Transform the document
        result = adapt_node(source_node, adapter_def)

        # Validate root document structure
        assert (
            result.type == "article"
        ), f"Root should be 'article', got '{result.type}'"
        assert (
            "The Article Title" in result.label
        ), f"Article title not found in '{result.label}'"
        assert len(result.children) > 0, "Article should have child elements"

        # Validate comprehensive node type coverage (test what actually exists)
        node_types = self._collect_node_types(result)
        essential_types = {"article", "section", "title", "simpara"}
        missing_essential = essential_types - node_types
        assert (
            not missing_essential
        ), f"Missing essential node types: {missing_essential}"

        # Optional types that may or may not be present depending on content
        optional_types = {
            "note",
            "abstract",
            "emphasis",
            "footnote",
            "indexterm",
            "table",
            "row",
            "entry",
        }
        found_optional = node_types.intersection(optional_types)
        assert (
            len(found_optional) > 0
        ), f"Should find some optional types, but found none. Available: {node_types}"

    def test_section_title_extraction(self):
        """Test that section titles are properly extracted with fallbacks."""
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")
        adapter_def = asdict(AdapterLib.get("asciidoc"))
        result = adapt_node(source_node, adapter_def)

        # Find all section nodes
        sections = self._find_nodes_by_type(result, "section")
        assert len(sections) > 0, "Should find section elements"

        # Check that sections have meaningful labels with section indicator
        for section in sections:
            assert section.label.startswith(
                "§ "
            ), f"Section label should start with '§ ', got '{section.label}'"
            assert (
                len(section.label) > 2
            ), "Section should have content beyond indicator"

    def test_list_processing_and_counting(self):
        """Test that lists are properly processed with item counting."""
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")
        adapter_def = asdict(AdapterLib.get("asciidoc"))
        result = adapt_node(source_node, adapter_def)

        # Find list elements
        all_nodes = self._flatten_nodes(result)
        list_nodes = [
            n
            for n in all_nodes
            if n.type in ["itemizedlist", "orderedlist", "variablelist"]
        ]

        if list_nodes:  # Only test if lists exist in test data
            for list_node in list_nodes:
                # Should have meaningful label indicating list type
                assert any(
                    word in list_node.label.lower()
                    for word in ["list", "items", "entries"]
                ), f"List label should indicate type: '{list_node.label}'"

    def test_text_content_truncation(self):
        """Test that long text content is properly truncated."""
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")
        adapter_def = asdict(AdapterLib.get("asciidoc"))
        result = adapt_node(source_node, adapter_def)

        # Find text-heavy elements like simpara
        text_nodes = self._find_nodes_by_type(result, "simpara")
        if text_nodes:
            long_text_nodes = [n for n in text_nodes if len(n.label) > 60]
            for node in long_text_nodes:
                assert node.label.endswith(
                    "..."
                ), f"Long text should be truncated: '{node.label}'"

    def test_ignore_types_functionality(self):
        """Test that specified node types are properly ignored."""
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")
        adapter_def = asdict(AdapterLib.get("asciidoc"))
        result = adapt_node(source_node, adapter_def)

        # Verify ignored types don't appear in final tree
        node_types = self._collect_node_types(result)
        ignored_types = {
            "articleinfo",
            "author",
            "authorinitials",
            "date",
            "revhistory",
        }
        found_ignored = node_types.intersection(ignored_types)
        assert (
            not found_ignored
        ), f"Found ignored types in result: {found_ignored}"

    def test_icon_mappings(self):
        """Test that nodes receive appropriate icons."""
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")
        adapter_def = asdict(AdapterLib.get("asciidoc"))
        result = adapt_node(source_node, adapter_def)

        # Check that common elements have icons
        icon_mappings = {
            "article": "📄",
            "section": "§",
            "para": "¶",
            "simpara": "¶",
        }

        for node_type, expected_icon in icon_mappings.items():
            nodes = self._find_nodes_by_type(result, node_type)
            if nodes:  # Only test if node type exists
                node = nodes[0]
                assert (
                    node.icon == expected_icon
                ), f"Node type '{node_type}' should have icon '{expected_icon}', got '{node.icon}'"

    def test_adapter_error_resilience(self):
        """Test adapter behavior with minimal XML structure."""
        # Create a temporary minimal XML file to test resilience
        import tempfile
        import os

        minimal_xml = """<?xml version="1.0"?>
        <article>
            <section>
                <simpara>Simple content</simpara>
            </section>
        </article>"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as f:
            f.write(minimal_xml)
            temp_path = f.name

        try:
            source_node = parse_document(temp_path, format_name="xml")
            adapter_def = asdict(AdapterLib.get("asciidoc"))
            result = adapt_node(source_node, adapter_def)

            # Should handle minimal structure gracefully
            assert result.type == "article"
            # The label should either be extracted or use a fallback
            assert result.label in [
                "AsciiDoc Document",
                "article",
            ], f"Unexpected label: '{result.label}'"
            assert len(result.children) > 0
        finally:
            os.unlink(temp_path)

    def test_transform_pipeline_functionality(self):
        """Test that transform pipelines work correctly for content processing."""
        test_data_path = (
            Path(__file__).parent / "test_data" / "asciidoc" / "article.xml"
        )
        source_node = parse_document(str(test_data_path), format_name="xml")
        adapter_def = asdict(AdapterLib.get("asciidoc"))
        result = adapt_node(source_node, adapter_def)

        # Find emphasis nodes which should have prefix/suffix transforms
        emphasis_nodes = self._find_nodes_by_type(result, "emphasis")
        if emphasis_nodes:
            for node in emphasis_nodes:
                assert node.label.startswith("_") and node.label.endswith(
                    "_"
                ), f"Emphasis should have underscores: '{node.label}'"
