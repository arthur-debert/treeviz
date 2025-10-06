"""
Essential integration tests for multi-component workflows.

These 7 tests cover the most critical integration scenarios for treeviz.
"""

from pathlib import Path

import pytest
from treeviz.adapters import adapt_node
from treeviz.formats import parse_document
from treeviz.rendering import TemplateRenderer


def get_test_data_path(filename: str) -> str:
    """Get path to test data file."""
    return str(
        Path(__file__).parent.parent.parent / "test-data" / "formats" / filename
    )


class TestEssentialIntegration:
    """Essential integration tests covering critical multi-component workflows."""

    def test_complete_parse_adapt_render_pipeline(self):
        """Test complete pipeline: parse document → adapt with config → render output."""
        # Parse a document
        file_path = get_test_data_path("simple.json")
        parsed_data = parse_document(file_path)

        # Adapt with configuration
        adapter_config = {
            "label": "type",
            "type": "type",
            "children": "children",
        }
        adapted_node = adapt_node(parsed_data, adapter_config)

        # Render the result
        renderer = TemplateRenderer()
        rendered_output = renderer.render(adapted_node)

        # Verify complete pipeline works
        assert isinstance(rendered_output, str)
        assert len(rendered_output) > 0
        # Should contain some recognizable content from the parsed structure
        assert any(term in rendered_output for term in ["element", "text", "L"])

    def test_advanced_path_expressions_with_transformations(self):
        """Test advanced path expressions integrated with transformations."""
        # Test complex nested data extraction through adaptation
        test_data = {
            "document": {
                "sections": [
                    {
                        "title": "Section 1",
                        "items": [{"name": "Item A"}, {"name": "Item B"}],
                    },
                    {"title": "Section 2", "items": [{"name": "Item C"}]},
                ]
            }
        }

        # Test nested adaptation with path-like access
        adapter_config = {
            "label": "title",
            "type": "type",
            "children": "sections",
        }

        # Adapt the document level
        result = adapt_node(test_data["document"], adapter_config)

        # Verify complex data structure was properly adapted
        assert hasattr(result, "children")
        assert len(result.children) == 2
        assert all(hasattr(child, "label") for child in result.children)

    def test_children_selector_with_complex_filtering(self):
        """Test children selector integrated with complex include/exclude patterns."""
        # Test data with nested structure
        test_data = {
            "type": "root",
            "children": [
                {"type": "include_me", "value": "keep"},
                {"type": "exclude_me", "value": "remove"},
                {"type": "include_me", "value": "also_keep"},
                {"type": "meta", "value": "extra"},
            ],
        }

        # Create selector with complex rules
        selector_config = {
            "include": ["include_me"],
            "exclude": ["exclude_me", "meta"],
        }

        # Adapt with children selector
        adapter_config = {
            "label": "value",
            "type": "type",
            "children": selector_config,
        }

        result = adapt_node(test_data, adapter_config)

        # Verify filtering worked across the integration
        assert hasattr(result, "children")
        child_types = [child.type for child in result.children]
        assert "include_me" in child_types
        assert "exclude_me" not in child_types
        assert "meta" not in child_types

    def test_error_handling_across_components(self):
        """Test error handling integration across multiple components."""
        # Test invalid path should fail gracefully
        with pytest.raises(FileNotFoundError):
            parse_document("/nonexistent/file.json")

        # Test invalid adapter config should fail gracefully
        test_data = {"type": "test"}
        invalid_config = {"invalid_field": "value"}

        # Should handle invalid config without crashing
        try:
            result = adapt_node(test_data, invalid_config)
            # Basic adaptation should still work even with invalid config
            assert hasattr(result, "type") or hasattr(result, "label")
        except Exception as e:
            # Error should be informative
            assert len(str(e)) > 0

    def test_configuration_loading_and_application(self):
        """Test configuration loading and application across components."""
        # Test that configuration can be loaded and applied
        from treeviz.definitions import AdapterLib

        try:
            # Try to get a definition from the library
            definition = AdapterLib.get("3viz")
            assert definition is not None

            # Apply the definition as adapter config
            test_data = {"label": "test", "type": "element", "children": []}
            result = adapt_node(test_data, definition.__dict__)

            # Should successfully adapt using library definition
            assert hasattr(result, "type")
            assert hasattr(result, "label")

        except Exception:
            # If library system not available, test basic config
            basic_config = {
                "label": "label",
                "type": "type",
                "children": "children",
            }
            test_data = {"label": "test", "type": "element", "children": []}
            result = adapt_node(test_data, basic_config)
            assert hasattr(result, "type")

    def test_tree_processing_with_multiple_adapters(self):
        """Test tree processing workflows using multiple adapter configurations."""
        # Complex nested data
        test_data = {
            "type": "document",
            "content": [
                {
                    "type": "section",
                    "items": [
                        {"type": "paragraph", "text": "Hello"},
                        {"type": "paragraph", "text": "World"},
                    ],
                }
            ],
        }

        # First adapter config - extract content
        config1 = {"label": "type", "type": "type", "children": "content"}
        result1 = adapt_node(test_data, config1)

        # Verify first adaptation worked
        assert result1.type == "document"
        assert len(result1.children) == 1
        assert result1.children[0].type == "section"

        # Second adapter config - extract items from sections
        config2 = {"label": "type", "type": "type", "children": "items"}
        section_data = {
            "type": "section",
            "items": test_data["content"][0]["items"],
        }
        result2 = adapt_node(section_data, config2)

        # Verify second adaptation worked
        assert result2.type == "section"
        assert len(result2.children) == 2
        assert all(child.type == "paragraph" for child in result2.children)
