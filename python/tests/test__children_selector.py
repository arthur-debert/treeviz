"""
Unit tests for ChildrenSelector functionality.

Tests the ChildrenSelector dataclass pattern matching methods in isolation.
"""

from dataclasses import asdict

from treeviz.definitions.model import Definition, ChildrenSelector


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
