"""
Test the extended load_document and load_adapter functions for Python object support.
"""

import pytest
from treeviz.formats import load_document
from treeviz.adapters.utils import load_adapter
from treeviz.definitions.model import Definition


class TestLoadDocumentExtensions:
    """Test load_document with Python objects."""

    def test_load_document_dict(self):
        """Test loading a dictionary object."""
        test_dict = {"type": "root", "name": "test", "children": []}
        result = load_document(test_dict)
        assert result is test_dict

    def test_load_document_list(self):
        """Test loading a list object."""
        test_list = [{"type": "item1"}, {"type": "item2"}]
        result = load_document(test_list)
        assert result is test_list

    def test_load_document_nested_structure(self):
        """Test loading a complex nested structure."""
        nested = {
            "type": "document",
            "children": [
                {"type": "paragraph", "content": "Hello"},
                {"type": "list", "items": [1, 2, 3]},
            ],
        }
        result = load_document(nested)
        assert result is nested

    def test_load_document_preserves_file_behavior(self):
        """Test that file loading still works (string inputs)."""
        # This should still be handled by the original logic
        # We're just testing that strings are passed through to the original path
        # The actual file loading is tested elsewhere

        # Test that string inputs don't trigger the new object logic
        import tempfile
        import json

        test_data = {"type": "test"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_document(temp_path)
            assert result == test_data
        finally:
            import os

            os.unlink(temp_path)


class TestLoadAdapterExtensions:
    """Test load_adapter with Python objects."""

    def test_load_adapter_dict(self):
        """Test loading an adapter from a dictionary."""
        adapter_dict = {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
            "icons": {"function": "⚡", "class": "🏛"},
        }

        def_dict, icons = load_adapter(adapter_dict)

        assert isinstance(def_dict, dict)
        assert isinstance(icons, dict)
        assert "function" in icons
        assert icons["function"] == "⚡"
        assert def_dict["label"] == "name"

    def test_load_adapter_definition_object(self):
        """Test loading an adapter from a Definition object."""
        definition_obj = Definition(
            label="title",
            type="kind",
            children="elements",
            icons={"paragraph": "¶", "heading": "§"},
        )

        def_dict, icons = load_adapter(definition_obj)

        assert isinstance(def_dict, dict)
        assert isinstance(icons, dict)
        assert "paragraph" in icons
        assert icons["paragraph"] == "¶"
        assert def_dict["label"] == "title"

    def test_load_adapter_dict_validation(self):
        """Test that invalid adapter dicts raise errors."""
        # Test completely invalid dict
        with pytest.raises(ValueError, match="Invalid adapter definition"):
            load_adapter({"invalid": "config"})

    def test_load_adapter_preserves_string_behavior(self):
        """Test that string adapter loading still works."""
        # Test built-in adapter
        def_dict, icons = load_adapter("3viz")
        assert isinstance(def_dict, dict)
        assert isinstance(icons, dict)

        # Test that unknown adapters still raise errors
        with pytest.raises(ValueError, match="Unknown adapter"):
            load_adapter("nonexistent_adapter")

    def test_load_adapter_type_error(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="adapter_spec must be"):
            load_adapter(123)  # Invalid type

    def test_load_adapter_dict_merges_with_defaults(self):
        """Test that dict adapters get merged with defaults properly."""
        minimal_dict = {"label": "custom_label"}

        def_dict, icons = load_adapter(minimal_dict)

        # Should have the custom label
        assert def_dict["label"] == "custom_label"

        # Should have default values for other fields
        assert "type" in def_dict
        assert "children" in def_dict
        assert isinstance(icons, dict)  # Should have default icons


class TestLoadIntegration:
    """Test that the extended functions work together."""

    def test_load_functions_integration(self):
        """Test using both extended functions together."""
        # Test data
        document = {
            "type": "root",
            "title": "My Document",
            "elements": [
                {"type": "paragraph", "title": "First paragraph"},
                {"type": "heading", "title": "A heading"},
            ],
        }

        adapter = {
            "label": "title",
            "type": "type",
            "children": "elements",
            "icons": {"paragraph": "¶", "heading": "§", "root": "⧉"},
        }

        # Load document (should pass through)
        doc = load_document(document)
        assert doc is document

        # Load adapter
        adapter_def, icons = load_adapter(adapter)
        assert isinstance(adapter_def, dict)
        assert "paragraph" in icons

        # Test conversion works
        from treeviz.adapters.utils import convert_document

        node = convert_document(doc, adapter_def)

        assert node.label == "My Document"
        assert node.type == "root"
        assert len(node.children) == 2
        assert node.children[0].label == "First paragraph"
        assert node.children[1].label == "A heading"
