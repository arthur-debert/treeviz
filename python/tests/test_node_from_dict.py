"""
Test the Node.from_dict method for JSON deserialization.
"""

import pytest
from treeviz.model import Node


class TestNodeFromDict:
    """Test Node.from_dict class method."""

    def test_from_dict_simple(self):
        """Test creating a Node from a simple dictionary."""
        data = {
            "label": "test node",
            "type": "test_type",
            "icon": "🔧",
            "content_lines": 5,
            "source_location": {"line": 10, "column": 5},
            "extra": {"custom": "data"},
            "children": [],
        }

        node = Node.from_dict(data)

        assert node.label == "test node"
        assert node.type == "test_type"
        assert node.icon == "🔧"
        assert node.content_lines == 5
        assert node.source_location == {"line": 10, "column": 5}
        assert node.extra == {"custom": "data"}
        assert node.children == []

    def test_from_dict_minimal(self):
        """Test creating a Node from minimal dictionary."""
        data = {"label": "minimal"}

        node = Node.from_dict(data)

        assert node.label == "minimal"
        assert node.type is None
        assert node.icon is None
        assert node.content_lines == 1
        assert node.source_location is None
        assert node.extra == {}
        assert node.children == []

    def test_from_dict_with_nested_children(self):
        """Test creating a Node with nested children."""
        data = {
            "label": "parent",
            "type": "parent_type",
            "children": [
                {
                    "label": "child1",
                    "type": "child_type",
                    "icon": "👶",
                    "children": [],
                },
                {
                    "label": "child2",
                    "type": "child_type",
                    "children": [
                        {
                            "label": "grandchild",
                            "type": "grandchild_type",
                            "children": [],
                        }
                    ],
                },
            ],
        }

        node = Node.from_dict(data)

        # Check parent
        assert node.label == "parent"
        assert len(node.children) == 2

        # Check first child
        child1 = node.children[0]
        assert isinstance(child1, Node)
        assert child1.label == "child1"
        assert child1.icon == "👶"
        assert len(child1.children) == 0

        # Check second child
        child2 = node.children[1]
        assert isinstance(child2, Node)
        assert child2.label == "child2"
        assert len(child2.children) == 1

        # Check grandchild
        grandchild = child2.children[0]
        assert isinstance(grandchild, Node)
        assert grandchild.label == "grandchild"
        assert grandchild.type == "grandchild_type"

    def test_from_dict_missing_label(self):
        """Test from_dict with missing label (should default to empty string)."""
        data = {"type": "test"}

        node = Node.from_dict(data)

        assert node.label == ""
        assert node.type == "test"

    def test_from_dict_type_error(self):
        """Test from_dict with invalid input type."""
        with pytest.raises(TypeError, match="Expected dict"):
            Node.from_dict("not a dict")

        with pytest.raises(TypeError, match="Expected dict"):
            Node.from_dict(123)

    def test_from_dict_empty_dict(self):
        """Test from_dict with empty dictionary."""
        node = Node.from_dict({})

        assert node.label == ""
        assert node.type is None
        assert node.children == []

    def test_from_dict_cli_format_compatibility(self):
        """Test that from_dict works with CLI's JSON output format."""
        # This is the actual format produced by CLI's asdict() + json.dumps()
        cli_format = {
            "label": "root",
            "type": "root",
            "icon": None,
            "content_lines": 1,
            "source_location": None,
            "extra": {},
            "children": [
                {
                    "label": "paragraph",
                    "type": "paragraph",
                    "icon": "¶",
                    "content_lines": 1,
                    "source_location": None,
                    "extra": {},
                    "children": [],
                }
            ],
        }

        node = Node.from_dict(cli_format)

        assert node.label == "root"
        assert node.type == "root"
        assert node.icon is None
        assert len(node.children) == 1

        child = node.children[0]
        assert isinstance(child, Node)
        assert child.label == "paragraph"
        assert child.icon == "¶"
        assert child.children == []

    def test_from_dict_roundtrip_with_asdict(self):
        """Test that from_dict + asdict is a roundtrip."""
        from dataclasses import asdict

        original = Node(
            label="test",
            type="test_type",
            icon="🧪",
            children=[Node(label="child", type="child_type", children=[])],
        )

        # Convert to dict and back
        dict_form = asdict(original)
        reconstructed = Node.from_dict(dict_form)

        # Should be equivalent
        assert reconstructed.label == original.label
        assert reconstructed.type == original.type
        assert reconstructed.icon == original.icon
        assert len(reconstructed.children) == len(original.children)
        assert reconstructed.children[0].label == original.children[0].label
