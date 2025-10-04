"""
Unit tests for load_adapter function.

Tests the adapter loading functionality including built-in adapters,
file-based adapters, format detection, and error handling.
"""

import json
import tempfile
import pytest

from treeviz.adapters.utils import load_adapter
from treeviz.formats import DocumentFormatError


class TestLoadAdapter:
    """Test cases for load_adapter function."""

    def test_load_adapter_3viz_builtin(self):
        """Test loading built-in 3viz adapter."""
        adapter_dict, icons_dict = load_adapter("3viz")

        # Should be a valid adapter dictionary
        assert isinstance(adapter_dict, dict)
        assert isinstance(icons_dict, dict)

        # Should have required fields
        assert "label" in adapter_dict
        assert "type" in adapter_dict
        assert "children" in adapter_dict
        assert "icons" in adapter_dict

        # Icons should contain basic icon mappings
        assert isinstance(icons_dict, dict)
        assert len(icons_dict) > 0

    def test_load_adapter_mdast_builtin(self):
        """Test loading built-in mdast adapter."""
        adapter_dict, icons_dict = load_adapter("mdast")

        # Should be a valid adapter dictionary
        assert isinstance(adapter_dict, dict)
        assert isinstance(icons_dict, dict)

        # Should have mdast-specific icons
        assert "paragraph" in icons_dict
        assert "heading" in icons_dict
        assert "list" in icons_dict

    def test_load_adapter_unist_builtin(self):
        """Test loading built-in unist adapter."""
        adapter_dict, icons_dict = load_adapter("unist")

        # Should be a valid adapter dictionary
        assert isinstance(adapter_dict, dict)
        assert isinstance(icons_dict, dict)

        # Should have unist-specific icons
        assert "element" in icons_dict or "root" in icons_dict

    def test_load_adapter_unknown_builtin(self):
        """Test loading unknown built-in adapter raises ValueError."""
        with pytest.raises(ValueError, match="Unknown adapter 'nonexistent'"):
            load_adapter("nonexistent")

    def test_load_adapter_json_file(self):
        """Test loading adapter from JSON file."""
        adapter_def = {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
            "icons": {"test_type": "🧪", "function": "⚡"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(adapter_def, f)
            f.flush()

            adapter_dict, icons_dict = load_adapter(f.name)

            assert adapter_dict["label"] == "name"
            assert adapter_dict["type"] == "node_type"
            assert adapter_dict["children"] == "child_nodes"
            assert "test_type" in icons_dict
            assert icons_dict["test_type"] == "🧪"

    def test_load_adapter_yaml_file(self):
        """Test loading adapter from YAML file."""
        yaml_content = """
label: title
type: kind
children: items
icons:
  yaml_type: "📄"
  config: "⚙️"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                adapter_dict, icons_dict = load_adapter(f.name)

                assert adapter_dict["label"] == "title"
                assert adapter_dict["type"] == "kind"
                assert adapter_dict["children"] == "items"
                assert "yaml_type" in icons_dict
                assert icons_dict["yaml_type"] == "📄"
            except DocumentFormatError as e:
                if "Unsupported format" in str(
                    e
                ) or "Cannot detect format" in str(e):
                    pytest.skip("YAML format not available")
                else:
                    raise

    def test_load_adapter_file_with_format_override(self):
        """Test loading adapter file with explicit format override."""
        adapter_def = {
            "label": "content",
            "type": "tag",
            "icons": {"override_test": "🔧"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".data", delete=False
        ) as f:
            json.dump(adapter_def, f)
            f.flush()

            adapter_dict, icons_dict = load_adapter(
                f.name, adapter_format="json"
            )

            assert adapter_dict["label"] == "content"
            assert adapter_dict["type"] == "tag"
            assert "override_test" in icons_dict

    def test_load_adapter_nonexistent_file(self):
        """Test loading nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="Adapter file not found"):
            load_adapter("/nonexistent/adapter.json")

    def test_load_adapter_invalid_json_file(self):
        """Test loading invalid JSON file raises DocumentFormatError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("invalid json content")
            f.flush()

            with pytest.raises(
                DocumentFormatError, match="Failed to parse adapter file"
            ):
                load_adapter(f.name)

    def test_load_adapter_non_dict_file(self):
        """Test loading file with non-dict content raises ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(["this", "is", "an", "array"], f)
            f.flush()

            with pytest.raises(ValueError, match="must contain a dictionary"):
                load_adapter(f.name)

    def test_load_adapter_invalid_adapter_definition(self):
        """Test loading file with invalid adapter definition raises ValueError."""
        # Missing required fields
        invalid_def = {"invalid_field": "value"}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(invalid_def, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid adapter definition"):
                load_adapter(f.name)

    def test_load_adapter_file_vs_name_detection(self):
        """Test that file paths are correctly distinguished from adapter names."""
        # These should be treated as file paths
        file_specs = [
            "/path/to/adapter.json",
            "./adapter.yaml",
            "adapter.json",
            "path/adapter.yaml",
            "..\\adapter.json",  # Windows path
        ]

        for spec in file_specs:
            with pytest.raises(ValueError, match="Adapter file not found"):
                load_adapter(spec)

        # These should be treated as adapter names
        name_specs = ["mdast", "unist", "3viz", "custom_adapter_name"]

        # mdast, unist, 3viz should work, custom should fail with unknown adapter
        for spec in name_specs:
            if spec in ["mdast", "unist", "3viz"]:
                adapter_dict, icons_dict = load_adapter(spec)
                assert isinstance(adapter_dict, dict)
                assert isinstance(icons_dict, dict)
            else:
                with pytest.raises(ValueError, match="Unknown adapter"):
                    load_adapter(spec)

    def test_load_adapter_returns_separate_icons(self):
        """Test that load_adapter returns icons separately from adapter definition."""
        adapter_dict, icons_dict = load_adapter("3viz")

        # Both should be dicts
        assert isinstance(adapter_dict, dict)
        assert isinstance(icons_dict, dict)

        # Icons should be in both places but should be separate objects
        assert "icons" in adapter_dict
        assert adapter_dict["icons"] == icons_dict
        assert adapter_dict["icons"] is not icons_dict  # Different objects

    def test_load_adapter_preserves_all_definition_fields(self):
        """Test that load_adapter preserves all definition fields from file."""
        complete_def = {
            "label": "title",
            "type": "node_type",
            "children": "child_list",
            "icon": "icon_field",
            "content_lines": "line_count",
            "source_location": "location",
            "extra": "metadata",
            "icons": {"custom": "🔥", "test": "✅"},
            "type_overrides": {"special": {"label": "special_name"}},
            "ignore_types": ["comment", "whitespace"],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(complete_def, f)
            f.flush()

            adapter_dict, icons_dict = load_adapter(f.name)

            # All fields should be preserved
            assert adapter_dict["label"] == "title"
            assert adapter_dict["type"] == "node_type"
            assert adapter_dict["children"] == "child_list"
            assert adapter_dict["icon"] == "icon_field"
            assert adapter_dict["content_lines"] == "line_count"
            assert adapter_dict["source_location"] == "location"
            assert adapter_dict["extra"] == "metadata"
            assert "special" in adapter_dict["type_overrides"]
            assert "comment" in adapter_dict["ignore_types"]

            # Icons should include custom icons
            assert "custom" in icons_dict
            assert icons_dict["custom"] == "🔥"


class TestLoadAdapterIntegration:
    """Integration tests for load_adapter with real definition files."""

    def test_load_adapter_minimal_valid_definition(self):
        """Test loading minimal valid adapter definition."""
        minimal_def = {
            "label": "name"
            # Other fields should get defaults
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(minimal_def, f)
            f.flush()

            adapter_dict, icons_dict = load_adapter(f.name)

            # Should have defaults applied
            assert adapter_dict["label"] == "name"
            assert adapter_dict["type"] == "type"  # default
            assert adapter_dict["children"] == "children"  # default
            assert len(icons_dict) > 0  # should have baseline icons

    def test_load_adapter_merges_with_defaults(self):
        """Test that file-based adapters merge with default icons."""
        custom_def = {"label": "title", "icons": {"custom_type": "🌟"}}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(custom_def, f)
            f.flush()

            adapter_dict, icons_dict = load_adapter(f.name)

            # Should have custom icon
            assert "custom_type" in icons_dict
            assert icons_dict["custom_type"] == "🌟"

            # Should also have default icons
            assert "dict" in icons_dict  # baseline icon
            assert "str" in icons_dict  # baseline icon
