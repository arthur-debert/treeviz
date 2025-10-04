"""
Integration tests for children selector functionality with adapter system.

NOTE: The unit tests for ChildrenSelector have been moved to:
test__children_selector.py

This file contains integration tests that test ChildrenSelector
in combination with the adapter system (adapt_node).
"""

from treeviz.adapters import adapt_node


class MockNode:
    """Mock node for testing adapter functionality."""

    def __init__(self, node_type, **kwargs):
        self.node_type = node_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestChildrenSelectorIntegration:
    """Test integration of ChildrenSelector with adapter system."""

    def test_adapt_node_with_children_selector_filtering(self):
        """Test that adapt_node properly filters children using ChildrenSelector."""
        # Create a mock source node with various child types
        source_node = MockNode(
            "session",
            # Add various attributes that might contain child nodes
            elements=[
                MockNode("paragraph", text="First paragraph"),
                MockNode("footer", text="Footer content"),
                MockNode("section", text="Section content"),
                MockNode("script", text="Script content"),
            ],
            metadata={"title": "Test Session"},
        )

        # Define adapter with ChildrenSelector
        def_dict = {
            "label": "text",
            "type": "node_type",
            "children": {
                "include": ["paragraph", "section"],
                "exclude": ["footer", "script"],
            },
        }

        result = adapt_node(source_node, def_dict)

        # Should have filtered to only paragraph and section children
        assert len(result.children) == 2
        child_types = [child.type for child in result.children]
        assert "paragraph" in child_types
        assert "section" in child_types
        assert "footer" not in child_types
        assert "script" not in child_types

    def test_adapt_node_with_children_selector_wildcard(self):
        """Test ChildrenSelector with wildcard patterns."""
        source_node = MockNode(
            "document",
            content=[
                MockNode("h1", text="Main heading"),
                MockNode("h2", text="Sub heading"),
                MockNode("paragraph", text="Content"),
                MockNode("footer", text="Footer"),
            ],
        )

        def_dict = {
            "label": "text",
            "type": "node_type",
            "children": {"include": ["h*", "paragraph"], "exclude": ["footer"]},
        }

        result = adapt_node(source_node, def_dict)

        assert len(result.children) == 3
        child_types = [child.type for child in result.children]
        assert "h1" in child_types
        assert "h2" in child_types
        assert "paragraph" in child_types
        assert "footer" not in child_types

    def test_adapt_node_fallback_to_traditional_children(self):
        """Test that string children attribute still works as before."""
        source_node = MockNode(
            "root",
            children=[
                MockNode("paragraph", text="First"),
                MockNode("paragraph", text="Second"),
            ],
        )

        def_dict = {
            "label": "text",
            "type": "node_type",
            "children": "children",  # Traditional string attribute
        }

        result = adapt_node(source_node, def_dict)

        assert len(result.children) == 2
        assert all(child.type == "paragraph" for child in result.children)

    def test_adapt_node_with_dict_structure(self):
        """Test that ChildrenSelector works with dictionary structures."""
        source_dict = {
            "type": "session",
            "label": "Session Title",
            "paragraph": {"type": "paragraph", "label": "Paragraph content"},
            "section": {"type": "section", "label": "Section content"},
            "footer": {"type": "footer", "label": "Footer content"},
        }

        def_dict = {
            "label": "label",
            "type": "type",
            "children": {
                "include": ["paragraph", "section"],
                "exclude": ["footer"],
            },
        }

        result = adapt_node(source_dict, def_dict)

        assert len(result.children) == 2
        child_types = [child.type for child in result.children]
        assert "paragraph" in child_types
        assert "section" in child_types
        assert "footer" not in child_types
