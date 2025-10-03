"""
Test children selector functionality for node-based filtering.

This module tests the new ChildrenSelector dataclass and its integration
with the adapter system.
"""

from dataclasses import asdict

from treeviz.definitions.model import Definition, ChildrenSelector
from treeviz.adapters import adapt_node


class TestChildrenSelector:
    """Test ChildrenSelector pattern matching functionality."""

    def test_children_selector_basic_patterns(self):
        """Test basic include/exclude patterns."""
        selector = ChildrenSelector(
            include=["paragraph", "section"], exclude=["footer"]
        )

        assert selector.matches("paragraph") is True
        assert selector.matches("section") is True
        assert selector.matches("footer") is False
        assert selector.matches("header") is False

    def test_children_selector_wildcard_patterns(self):
        """Test wildcard patterns with * character."""
        selector = ChildrenSelector(
            include=["h*", "section"], exclude=["hidden*"]
        )

        assert selector.matches("h1") is True
        assert selector.matches("h2") is True
        assert selector.matches("heading") is True
        assert selector.matches("section") is True
        assert selector.matches("hidden_element") is False
        assert selector.matches("hidden") is False
        assert selector.matches("paragraph") is False

    def test_children_selector_star_include_with_exclude(self):
        """Test star include pattern with specific excludes."""
        selector = ChildrenSelector(include=["*"], exclude=["footer", "script"])

        assert selector.matches("paragraph") is True
        assert selector.matches("section") is True
        assert selector.matches("div") is True
        assert selector.matches("footer") is False
        assert selector.matches("script") is False

    def test_children_selector_empty_or_none_type(self):
        """Test handling of empty or None node types."""
        selector = ChildrenSelector(include=["*"], exclude=[])

        assert selector.matches("") is False
        assert selector.matches(None) is False

    def test_definition_from_dict_with_children_selector(self):
        """Test Definition.from_dict properly converts children dict to ChildrenSelector."""
        def_dict = {
            "label": "text",
            "type": "node_type",
            "children": {
                "include": ["paragraph", "section", "h*"],
                "exclude": ["footer"],
            },
        }

        definition = Definition.from_dict(def_dict)

        assert isinstance(definition.children, ChildrenSelector)
        assert definition.children.include == ["paragraph", "section", "h*"]
        assert definition.children.exclude == ["footer"]

    def test_definition_from_dict_with_string_children(self):
        """Test Definition.from_dict preserves string children attribute."""
        def_dict = {
            "label": "text",
            "type": "node_type",
            "children": "child_nodes",
        }

        definition = Definition.from_dict(def_dict)

        assert isinstance(definition.children, str)
        assert definition.children == "child_nodes"

    def test_definition_serialization_with_children_selector(self):
        """Test that ChildrenSelector properly serializes to dict."""
        def_dict = {
            "children": {
                "include": ["paragraph", "section"],
                "exclude": ["footer"],
            }
        }

        definition = Definition.from_dict(def_dict)
        serialized = asdict(definition)

        assert serialized["children"]["include"] == ["paragraph", "section"]
        assert serialized["children"]["exclude"] == ["footer"]


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
