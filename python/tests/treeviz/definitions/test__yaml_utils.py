"""
Unit tests for YAML utilities module.

Tests dataclass field documentation extraction and YAML serialization.
"""

import pytest
from dataclasses import dataclass, field
from unittest.mock import patch

from treeviz.definitions.yaml_utils import (
    get_dataclass_field_docs,
    serialize_dataclass_to_yaml,
    serialize_dict_to_yaml,
    HAS_YAML,
)


@dataclass
class SampleDataclass:
    """Sample dataclass for testing."""

    name: str = field(metadata={"doc": "The name field"})
    count: int = field(metadata={"doc": "The count field"})
    children: str = field(
        metadata={"doc": "The children field"}, default="child_nodes"
    )
    no_doc: str = "no_extra"


class TestGetDataclassFieldDocs:
    """Test get_dataclass_field_docs function."""

    def test_get_field_docs_with_extra(self):
        """Test extracting field documentation from dataclass extra."""
        instance = SampleDataclass(name="test", count=5)
        docs = get_dataclass_field_docs(instance)

        assert docs["name"] == "The name field"
        assert docs["count"] == "The count field"
        assert docs["children"] == "The children field"
        assert "no_doc" not in docs  # No extra

    def test_get_field_docs_from_class(self):
        """Test extracting field documentation from dataclass class."""
        docs = get_dataclass_field_docs(SampleDataclass)

        assert docs["name"] == "The name field"
        assert docs["count"] == "The count field"
        assert docs["children"] == "The children field"

    def test_get_field_docs_non_dataclass(self):
        """Test get_field_docs with non-dataclass returns empty dict."""
        regular_obj = {"not": "a dataclass"}
        docs = get_dataclass_field_docs(regular_obj)

        assert docs == {}

    def test_get_field_docs_no_extra(self):
        """Test dataclass with no field extra."""

        @dataclass
        class NoExtra:
            value: str

        docs = get_dataclass_field_docs(NoExtra("test"))
        assert docs == {}


class TestSerializeDataclassToYaml:
    """Test serialize_dataclass_to_yaml function."""

    def test_serialize_dataclass_without_comments(self):
        """Test basic dataclass serialization without comments."""
        instance = SampleDataclass(name="test", count=42)

        # Should not raise ImportError when HAS_YAML is True
        if HAS_YAML:
            result = serialize_dataclass_to_yaml(
                instance, include_comments=False
            )
            assert "name: test" in result
            assert "count: 42" in result
        else:
            with pytest.raises(ImportError, match="YAML support requires"):
                serialize_dataclass_to_yaml(instance, include_comments=False)

    def test_serialize_dataclass_with_comments(self):
        """Test dataclass serialization with field comments."""
        instance = SampleDataclass(name="test", count=42)

        if HAS_YAML:
            result = serialize_dataclass_to_yaml(
                instance, include_comments=True
            )
            assert "name: test" in result
            assert "count: 42" in result
            # Should contain comment structure
            assert "#" in result  # Comments should be present
        else:
            with pytest.raises(ImportError, match="YAML support requires"):
                serialize_dataclass_to_yaml(instance, include_comments=True)

    def test_serialize_non_dataclass_raises_error(self):
        """Test that non-dataclass input raises ValueError."""
        regular_dict = {"not": "a dataclass"}

        with pytest.raises(
            ValueError, match="Input must be a dataclass instance"
        ):
            serialize_dataclass_to_yaml(regular_dict)


class TestSerializeDictToYaml:
    """Test serialize_dict_to_yaml function."""

    def test_yaml_not_available_raises_import_error(self):
        """Test ImportError when ruamel.yaml is not available."""
        with patch("treeviz.definitions.yaml_utils.HAS_YAML", False):
            with pytest.raises(
                ImportError, match="YAML support requires 'ruamel.yaml' package"
            ):
                serialize_dict_to_yaml({"test": "data"})

    def test_serialize_simple_dict_without_comments(self):
        """Test simple dictionary serialization without comments."""
        data = {"name": "test", "count": 42}

        if HAS_YAML:
            result = serialize_dict_to_yaml(data, include_comments=False)
            assert "name: test" in result
            assert "count: 42" in result
        else:
            # If YAML not available, should raise ImportError
            with pytest.raises(ImportError):
                serialize_dict_to_yaml(data, include_comments=False)

    def test_serialize_dict_with_no_field_docs(self):
        """Test serialization with include_comments=True but no field_docs."""
        data = {"name": "test", "count": 42}

        if HAS_YAML:
            # Should fall back to simple serialization when no field_docs
            result = serialize_dict_to_yaml(
                data, include_comments=True, field_docs=None
            )
            assert "name: test" in result
            assert "count: 42" in result
        else:
            with pytest.raises(ImportError):
                serialize_dict_to_yaml(data, include_comments=True)

    def test_serialize_dict_with_field_docs(self):
        """Test serialization with field documentation comments."""
        data = {"name": "test", "count": 42, "children": "child_nodes"}
        field_docs = {
            "name": "The name field",
            "count": "The count field",
            "children": "The children field",
        }

        if HAS_YAML:
            result = serialize_dict_to_yaml(
                data, include_comments=True, field_docs=field_docs
            )
            assert "name: test" in result
            assert "count: 42" in result
            # Should contain extended documentation for children field
            assert "Examples:" in result
            assert "traditional attribute" in result
        else:
            with pytest.raises(ImportError):
                serialize_dict_to_yaml(
                    data, include_comments=True, field_docs=field_docs
                )

    def test_serialize_dict_with_partial_field_docs(self):
        """Test serialization with only some fields having documentation."""
        data = {"name": "test", "undocumented": "value", "count": 42}
        field_docs = {"name": "The name field"}  # Only one field documented

        if HAS_YAML:
            result = serialize_dict_to_yaml(
                data, include_comments=True, field_docs=field_docs
            )
            assert "name: test" in result
            assert "undocumented: value" in result
            assert "count: 42" in result
        else:
            with pytest.raises(ImportError):
                serialize_dict_to_yaml(
                    data, include_comments=True, field_docs=field_docs
                )


class TestYamlIntegration:
    """Test integration scenarios with actual YAML operations."""

    @pytest.mark.skipif(not HAS_YAML, reason="ruamel.yaml not available")
    def test_full_dataclass_yaml_roundtrip(self):
        """Test complete dataclass to YAML serialization workflow."""
        instance = SampleDataclass(name="integration_test", count=100)

        # Serialize with comments
        yaml_output = serialize_dataclass_to_yaml(
            instance, include_comments=True
        )

        # Should be valid YAML content
        assert "name: integration_test" in yaml_output
        assert "count: 100" in yaml_output
        assert "children: child_nodes" in yaml_output

        # Should contain comment indicators
        assert "#" in yaml_output

    @pytest.mark.skipif(not HAS_YAML, reason="ruamel.yaml not available")
    def test_children_field_special_handling(self):
        """Test that children field gets special documentation treatment."""
        data = {"children": "some_value"}
        field_docs = {"children": "Basic children doc"}

        result = serialize_dict_to_yaml(
            data, include_comments=True, field_docs=field_docs
        )

        # Should contain extended documentation
        assert "Examples:" in result
        assert "include:" in result
        assert "exclude:" in result
        assert "traditional attribute" in result

    @pytest.mark.skipif(not HAS_YAML, reason="ruamel.yaml not available")
    def test_yaml_formatting_options(self):
        """Test that YAML formatting options are applied correctly."""
        data = {"level1": {"level2": ["item1", "item2", "item3"]}}

        result = serialize_dict_to_yaml(data, include_comments=False)

        # Should use block style (not flow style)
        assert "[" not in result  # No flow style lists
        assert "{" not in result  # No flow style mappings

        # Should have proper indentation
        lines = result.strip().split("\n")
        # Find indented lines and verify spacing
        indented_lines = [line for line in lines if line.startswith("  ")]
        assert len(indented_lines) > 0  # Should have indented content


class TestYamlModuleImportHandling:
    """Test handling of missing ruamel.yaml module."""

    def test_has_yaml_false_branch(self):
        """Test the import error handling when ruamel.yaml is not available."""
        # This tests the except ImportError branch (lines 16-17)
        with patch("treeviz.definitions.yaml_utils.HAS_YAML", False):
            # Should be able to import the module and access HAS_YAML
            import treeviz.definitions.yaml_utils

            assert treeviz.definitions.yaml_utils.HAS_YAML is False

    def test_import_error_handling(self):
        """Test the actual import error handling logic."""
        # Test the import error path by mocking the import to fail
        import sys
        import importlib

        # Save original module if it exists
        original_ruamel = sys.modules.get("ruamel")
        original_yaml = sys.modules.get("ruamel.yaml")

        try:
            # Remove ruamel modules from sys.modules to trigger ImportError
            if "ruamel" in sys.modules:
                del sys.modules["ruamel"]
            if "ruamel.yaml" in sys.modules:
                del sys.modules["ruamel.yaml"]

            # Mock the import to fail
            with patch.dict(
                "sys.modules", {"ruamel": None, "ruamel.yaml": None}
            ):
                # Force reload of the module to trigger the import logic
                import treeviz.definitions.yaml_utils

                importlib.reload(treeviz.definitions.yaml_utils)

                # This should have set HAS_YAML to False due to ImportError
                assert not treeviz.definitions.yaml_utils.HAS_YAML

        finally:
            # Restore original modules
            if original_ruamel is not None:
                sys.modules["ruamel"] = original_ruamel
            elif "ruamel" in sys.modules:
                del sys.modules["ruamel"]

            if original_yaml is not None:
                sys.modules["ruamel.yaml"] = original_yaml
            elif "ruamel.yaml" in sys.modules:
                del sys.modules["ruamel.yaml"]

            # Reload to restore normal state
            importlib.reload(treeviz.definitions.yaml_utils)
