"""
Tests for definition management.
"""

import json
import tempfile
import pytest
from pathlib import Path
from dataclasses import asdict

from treeviz.definitions import (
    load_def,
    Lib,
)
from treeviz.definitions.schema import Definition


def test_load_def_from_dict():
    """Test loading definition from dictionary."""
    def_dict = {"label": "name", "type": "node_type"}

    result = load_def(def_dict=def_dict)
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
        result = load_def(def_path=temp_path)
        # Check that user def_ was merged with defaults
        assert result["label"] == "name"  # User override
        assert result["type"] == "node_type"  # User override
        assert result["children"] == "children"  # Default
        assert result["icons"]["test"] == "⧉"  # User override
        # Note: Default icons are NOT merged in load_def - they're merged in adapter
        assert "type_overrides" in result  # Default included
        assert "ignore_types" in result  # Default included
    finally:
        Path(temp_path).unlink()


def test_load_def_file_not_found():
    """Test error when definition file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_def(def_path="/nonexistent/path.json")


def test_load_def_invalid_json():
    """Test error when definition file has invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(json.JSONDecodeError):
            load_def(def_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_def_both_sources():
    """Test error when both def_path and def_dict are provided."""
    with pytest.raises(ValueError, match="Cannot specify both"):
        load_def(
            def_path="test.json",
            def_dict={"label": "name"},
        )


def test_load_def_no_sources():
    """Test that default definition is returned when no sources are provided."""
    result = load_def()
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

    definition = Definition.from_dict(def_)
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
    definition = Definition.from_dict(user_data)

    # User values override defaults
    assert definition.label == "custom_name"
    assert definition.type == "custom_type"
    assert definition.children == "children"  # Default remains

    # Icons merge with baseline
    assert definition.icons["custom"] == "★"
    assert "unknown" in definition.icons  # baseline icon


def test_definition_from_dict_empty():
    """Test creating definition from empty dict uses all defaults."""
    definition = Definition.from_dict({})

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

    definition = Definition.from_dict(user_data)

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
    Definition.from_dict(def_)


def test_builtin_defs_exist():
    """Test that built-in definitions exist and are valid."""
    # Test that we can load known builtin configs
    mdast_def = asdict(Lib.get("mdast"))
    assert "label" in mdast_def
    assert "type" in mdast_def
    assert "children" in mdast_def
    json_def = asdict(Lib.get("json"))
    assert "label" in json_def
    assert "type" in json_def
    assert "children" in json_def


def test_lib_get_format():
    """Test loading format definition via Lib.get."""
    def_ = asdict(Lib.get("json"))

    assert "label" in def_
    assert "type" in def_
    assert "children" in def_
    assert "type_overrides" in def_
    assert "ignore_types" in def_
    # Note: icons come from const.py and are merged automatically


def test_lib_get_unknown():
    """Test error when requesting unknown format definition."""
    with pytest.raises(KeyError, match="Unknown format 'unknown'"):
        Lib.get("unknown")
