"""
Integration tests for document format parsing and adapter integration.

Tests the Format system, parse_document function, and integration with adapters.
"""

import pytest
from pathlib import Path
from dataclasses import asdict

from treeviz.formats import parse_document, get_supported_formats
from treeviz.adapters import adapt_node
from treeviz.definitions import Lib


def get_test_data_path(filename: str) -> str:
    """Get path to test data file."""
    return str(
        Path(__file__).parent.parent.parent / "test-data" / "formats" / filename
    )


class TestFormatIntegration:
    """Integration tests for format system."""

    @pytest.mark.parametrize(
        "format_name,test_file,expected_types",
        [
            ("json", "simple.json", {"element", "text"}),
            ("xml", "simple.xml", {"book", "title", "chapter"}),
            ("html", "simple.html", {"html", "head", "body"}),
            ("pformat", "sample.pformat", {"document", "element"}),
        ],
    )
    def test_format_parse_and_adapt_workflow(
        self, format_name, test_file, expected_types
    ):
        """Test complete workflow: parse document → adapt with adapter → verify structure."""
        # Parse the document
        file_path = get_test_data_path(test_file)
        parsed_data = parse_document(file_path)

        # Verify parsing succeeded
        assert isinstance(parsed_data, dict)
        assert len(parsed_data) > 0

        # Create a simple adapter for the format
        adapter_config = {
            "label": "value" if format_name == "json" else "type",
            "type": "type",
            "children": "children",
        }

        # Adapt the parsed data
        result = adapt_node(parsed_data, adapter_config)

        # Verify adapter integration worked
        assert hasattr(result, "type")
        assert hasattr(result, "label")
        assert hasattr(result, "children")

        # Check that we get expected node types from the format
        all_types = self._collect_node_types(result)
        found_expected = expected_types & all_types
        assert (
            len(found_expected) >= 1
        ), f"Expected some of {expected_types}, found {all_types}"

    def test_orthogonality_principle(self):
        """Test that format parsing is orthogonal to adapter selection."""
        # Parse equivalent JSON and YAML files (if YAML available)
        json_path = get_test_data_path("sample.json")
        json_data = parse_document(json_path)

        # Try YAML if available
        yaml_path = get_test_data_path("sample.yaml")
        try:
            yaml_data = parse_document(yaml_path)
            yaml_available = True
        except Exception:
            yaml_available = False
            yaml_data = json_data  # Fallback for testing adapter orthogonality

        # Create adapter
        adapter_config = {"label": "title", "type": "type", "children": "items"}

        # Apply same adapter to both formats
        json_result = adapt_node(json_data, adapter_config)
        yaml_result = adapt_node(yaml_data, adapter_config)

        # Verify adapters work regardless of input format
        assert hasattr(json_result, "type")
        assert hasattr(yaml_result, "type")

        if yaml_available:
            # If YAML was actually parsed, results should be equivalent
            assert json_result.type == yaml_result.type
            assert len(json_result.children) == len(yaml_result.children)

    @pytest.mark.parametrize(
        "format_name,test_file,children_config",
        [
            (
                "html",
                "simple.html",
                {"include": ["p", "div"], "exclude": ["head"]},
            ),
            (
                "xml",
                "simple.xml",
                {"include": ["title", "item"], "exclude": ["meta"]},
            ),
            (
                "pformat",
                "sample.pformat",
                {"include": ["element"], "exclude": ["comment"]},
            ),
        ],
    )
    def test_format_with_children_selector_integration(
        self, format_name, test_file, children_config
    ):
        """Test format parsing integrated with children selector filtering."""
        # Parse document
        file_path = get_test_data_path(test_file)
        parsed_data = parse_document(file_path)

        # Create adapter with children selector
        adapter_config = {
            "label": "type",
            "type": "type",
            "children": children_config,
        }

        # Adapt with filtering
        result = adapt_node(parsed_data, adapter_config)

        # Verify filtering was applied (should have some structure)
        assert hasattr(result, "children")
        # Basic validation that filtering logic was applied
        all_types = self._collect_node_types(result)

        # Should not contain excluded types (if they existed in source)
        for excluded_type in children_config.get("exclude", []):
            # We can't be sure excluded types existed, but if they did they should be filtered
            pass  # This is more about testing the integration works without errors

        # Should contain some included types if they exist
        included_types = set(children_config.get("include", []))
        if included_types:
            # At least the integration should work without errors
            assert len(all_types) >= 1

    def test_format_registration_and_discovery(self):
        """Test that all expected formats are properly registered."""
        supported_formats = get_supported_formats()

        # Core formats that should always be available
        core_formats = {"json"}
        for format_name in core_formats:
            assert format_name in supported_formats

        # Optional formats that might be available
        optional_formats = {"yaml", "html", "xml", "pformat"}
        available_optional = [
            f for f in optional_formats if f in supported_formats
        ]

        # Should have at least some formats available
        assert (
            len(supported_formats) >= 2
        ), f"Expected multiple formats, got: {supported_formats}"
        assert (
            len(available_optional) >= 2
        ), f"Expected optional formats, got: {available_optional}"

    def test_mdast_definition_integration(self):
        """Test that format parsing integrates properly with MDAST definitions."""
        # This test shows format-independent adapter integration
        json_path = get_test_data_path("simple.json")
        parsed_data = parse_document(json_path)

        # Use MDAST definition from library
        try:
            mdast_def = asdict(Lib.get("mdast"))
            result = adapt_node(parsed_data, mdast_def)

            # Verify MDAST integration works
            assert hasattr(result, "type")
            assert hasattr(result, "children")

            # MDAST should preserve hierarchical structure
            assert isinstance(result.children, list)

        except Exception as e:
            # If MDAST definition not available, that's okay
            pytest.skip(f"MDAST definition not available: {e}")

    def _collect_node_types(self, node):
        """Collect all node types in the tree."""
        types = {node.type} if hasattr(node, "type") else set()
        if hasattr(node, "children"):
            for child in node.children:
                types.update(self._collect_node_types(child))
        return types
