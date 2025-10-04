"""
Tests for definition management.
"""

import json
import tempfile
import pytest
from pathlib import Path
from dataclasses import asdict

from treeviz.definitions import AdapterLib, AdapterDef


def test_load_def_from_dict():
    """Test loading definition from dictionary."""
    def_dict = {"label": "name", "type": "node_type"}
    definition = AdapterDef.from_dict(def_dict)
    result = asdict(definition)
    # Check that user def_ was merged with defaults
    assert result["label"] == "name"  # User override
    assert result["type"] == "node_type"  # User override
    assert result["children"] == "children"  # Default
    assert "icons" in result  # Default included
    assert "type_overrides" in result  # Default included
    assert "ignore_types" in result  # Default included


def test_load_def_from_file():
    """Test loading definition from JSON file."""
    def_dict = {
        "label": "name",
        "type": "node_type",
        "icons": {"test": "⧉"},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(def_dict, f)
        temp_path = f.name

    try:
        # Load JSON and create AdapterDef
        with open(temp_path) as f:
            data = json.load(f)
        definition = AdapterDef.from_dict(data)
        result = asdict(definition)
        # Check that user def_ was merged with defaults
        assert result["label"] == "name"  # User override
        assert result["type"] == "node_type"  # User override
        assert result["children"] == "children"  # Default
        assert result["icons"]["test"] == "⧉"  # User override
        # Note: Default icons are merged in AdapterDef.from_dict
        assert "type_overrides" in result  # Default included
        assert "ignore_types" in result  # Default included
    finally:
        Path(temp_path).unlink()


def test_load_def_file_not_found():
    """Test error when definition file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        with open("/nonexistent/path.json") as f:
            json.load(f)


def test_load_def_invalid_json():
    """Test error when definition file has invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(json.JSONDecodeError):
            with open(temp_path) as f:
                json.load(f)
    finally:
        Path(temp_path).unlink()


def test_definition_default_constructor():
    """Test that default definition constructor returns proper defaults."""
    definition = AdapterDef()
    result = asdict(definition)
    # Should return default definition
    assert "label" in result
    assert "type" in result
    assert "children" in result
    assert "icons" in result
    assert "type_overrides" in result
    assert "ignore_types" in result
    # Check that we got the expected defaults
    assert result["label"] == "label"
    assert result["type"] == "type"
    assert result["children"] == "children"


def test_validate_def_valid():
    """Test validation of valid definition."""
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "child_nodes",
        "icons": {"test": "⧉"},
        "type_overrides": {"text": {"label": "content"}},
        "ignore_types": ["comment"],
    }

    definition = AdapterDef.from_dict(def_)
    result = asdict(definition)
    # Icons should now include baseline icons + user icons
    assert result["label"] == def_["label"]
    assert result["type"] == def_["type"]
    assert result["children"] == def_["children"]
    assert result["type_overrides"] == def_["type_overrides"]
    assert result["ignore_types"] == def_["ignore_types"]
    # Check that user icons are preserved
    assert result["icons"]["test"] == "⧉"
    # Check that baseline icons are included
    assert "unknown" in result["icons"]


def test_definition_from_dict_with_overrides():
    """Test creating definition with user overrides."""
    user_data = {
        "label": "custom_name",
        "type": "custom_type",
        "icons": {"custom": "★"},
    }
    definition = AdapterDef.from_dict(user_data)

    # User values override defaults
    assert definition.label == "custom_name"
    assert definition.type == "custom_type"
    assert definition.children == "children"  # Default remains

    # Icons merge with baseline
    assert definition.icons["custom"] == "★"
    assert "unknown" in definition.icons  # baseline icon


def test_definition_from_dict_empty():
    """Test creating definition from empty dict uses all defaults."""
    definition = AdapterDef.from_dict({})

    # Should have all default values
    assert definition.label == "label"
    assert definition.type == "type"
    assert definition.children == "children"
    assert "unknown" in definition.icons
    assert definition.type_overrides == {}
    assert definition.ignore_types == []


def test_definition_from_dict_merge_behavior():
    """Test that from_dict properly merges user data with defaults."""
    user_data = {
        "label": "custom_label",
        "type": "custom_type",
        "icons": {"paragraph": "§"},  # Override existing
        "type_overrides": {"text": {"label": "content"}},
        "ignore_types": ["comment"],
    }

    definition = AdapterDef.from_dict(user_data)

    # User values override defaults
    assert definition.label == "custom_label"
    assert definition.type == "custom_type"
    assert definition.children == "children"  # Default remains

    # Icons should merge with baseline
    assert definition.icons["paragraph"] == "§"  # User override
    assert "unknown" in definition.icons  # Still has baseline

    # Other fields should use user values
    assert definition.type_overrides == {"text": {"label": "content"}}
    assert definition.ignore_types == ["comment"]


def test_create_sample_def():
    """Test creation of sample definition."""
    # Use inline sample definition instead of external file
    def_ = {
        "label": "name",
        "type": "node_type",
        "children": "children",
        "icons": {"document": "⧉", "paragraph": "¶", "heading": "⊤"},
        "type_overrides": {"paragraph": {"label": "content"}},
        "ignore_types": ["comment", "whitespace"],
    }

    assert "label" in def_
    assert "type" in def_
    assert "children" in def_
    assert "icons" in def_
    assert "type_overrides" in def_
    assert "ignore_types" in def_

    # Should be valid
    AdapterDef.from_dict(def_)


def test_builtin_defs_exist():
    """Test that built-in definitions exist and are valid."""
    # Test that we can load known builtin configs
    mdast_def = asdict(AdapterLib.get("mdast"))
    assert "label" in mdast_def
    assert "type" in mdast_def
    assert "children" in mdast_def
    json_def = asdict(AdapterLib.get("unist"))
    assert "label" in json_def
    assert "type" in json_def
    assert "children" in json_def


def test_lib_get_unknown():
    """Test error when requesting unknown format definition."""
    with pytest.raises(KeyError, match="Unknown format 'unknown'"):
        AdapterLib.get("unknown")
