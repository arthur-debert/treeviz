"""
Tests for definition management.
"""

import json
import tempfile
import pytest
from pathlib import Path

from treeviz.definitions import (
    load_def,
    validate_def,
    get_builtin_def,
    _load_def_file,
    ConversionError,
)


def test_load_def_from_dict():
    """Test loading definition from dictionary."""
    def_dict = {"attributes": {"label": "name", "type": "node_type"}}

    result = load_def(def_dict=def_dict)
    # Check that user def_ was merged with defaults
    assert result["attributes"]["label"] == "name"  # User override
    assert result["attributes"]["type"] == "node_type"  # User override
    assert result["attributes"]["children"] == "children"  # Default
    assert "icon_map" in result  # Default included
    assert "type_overrides" in result  # Default included
    assert "ignore_types" in result  # Default included


def test_load_def_from_file():
    """Test loading definition from JSON file."""
    def_dict = {
        "attributes": {"label": "name", "type": "node_type"},
        "icon_map": {"test": "⧉"},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(def_dict, f)
        temp_path = f.name

    try:
        result = load_def(def_path=temp_path)
        # Check that user def_ was merged with defaults
        assert result["attributes"]["label"] == "name"  # User override
        assert result["attributes"]["type"] == "node_type"  # User override
        assert result["attributes"]["children"] == "children"  # Default
        assert result["icon_map"]["test"] == "⧉"  # User override
        assert "document" in result["icon_map"]  # Default icons included
        assert "type_overrides" in result  # Default included
        assert "ignore_types" in result  # Default included
    finally:
        Path(temp_path).unlink()


def test_load_def_file_not_found():
    """Test error when definition file doesn't exist."""
    with pytest.raises(ConversionError, match="Configuration file not found"):
        load_def(def_path="/nonexistent/path.json")


def test_load_def_invalid_json():
    """Test error when definition file has invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(ConversionError, match="Invalid JSON"):
            load_def(def_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_def_both_sources():
    """Test error when both def_path and def_dict are provided."""
    with pytest.raises(ConversionError, match="Cannot specify both"):
        load_def(
            def_path="test.json",
            def_dict={"attributes": {"label": "name"}},
        )


def test_load_def_no_sources():
    """Test that default definition is returned when no sources are provided."""
    result = load_def()
    # Should return default definition
    assert "attributes" in result
    assert "icon_map" in result
    assert "type_overrides" in result
    assert "ignore_types" in result
    # Check that we got the expected defaults
    assert result["attributes"]["label"] == "label"
    assert result["attributes"]["type"] == "type"
    assert result["attributes"]["children"] == "children"


def test_validate_def_valid():
    """Test validation of valid definition."""
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        },
        "icon_map": {"test": "⧉"},
        "type_overrides": {"text": {"label": "content"}},
        "ignore_types": ["comment"],
    }

    result = validate_def(def_)
    assert result == def_


def test_validate_def_not_dict():
    """Test validation error when def_ is not a dictionary."""
    with pytest.raises(ConversionError, match="must be a dictionary"):
        validate_def("not a dict")


def test_validate_def_missing_attributes():
    """Test validation error when attributes section is missing."""
    with pytest.raises(ConversionError, match="must include 'attributes'"):
        validate_def({})


def test_validate_def_attributes_not_dict():
    """Test validation error when attributes is not a dictionary."""
    with pytest.raises(
        ConversionError, match="'attributes' section must be a dictionary"
    ):
        validate_def({"attributes": "not a dict"})


def test_validate_def_missing_label():
    """Test validation error when label extraction is not specified."""
    with pytest.raises(
        ConversionError, match="must specify how to extract 'label'"
    ):
        validate_def({"attributes": {"type": "node_type"}})


def test_validate_def_invalid_icon_map():
    """Test validation error when icon_map is not a dictionary."""
    def_ = {"attributes": {"label": "name"}, "icon_map": "not a dict"}

    with pytest.raises(
        ConversionError, match="'icon_map' must be a dictionary"
    ):
        validate_def(def_)


def test_validate_def_invalid_type_overrides():
    """Test validation error when type_overrides is not a dictionary."""
    def_ = {"attributes": {"label": "name"}, "type_overrides": "not a dict"}

    with pytest.raises(
        ConversionError, match="'type_overrides' must be a dictionary"
    ):
        validate_def(def_)


def test_validate_def_invalid_ignore_types():
    """Test validation error when ignore_types is not a list."""
    def_ = {"attributes": {"label": "name"}, "ignore_types": "not a list"}

    with pytest.raises(ConversionError, match="'ignore_types' must be a list"):
        validate_def(def_)


def test_validate_def_invalid_type_override_value():
    """Test validation error when type override value is not a dictionary."""
    def_ = {
        "attributes": {"label": "name"},
        "type_overrides": {"text": "not a dict"},
    }

    with pytest.raises(
        ConversionError, match="Type override for 'text' must be a dictionary"
    ):
        validate_def(def_)


def test_create_sample_def():
    """Test creation of sample definition."""
    def_ = _load_def_file("sample.json")

    assert "attributes" in def_
    assert "label" in def_["attributes"]
    assert "icon_map" in def_
    assert "type_overrides" in def_
    assert "ignore_types" in def_

    # Should be valid
    validate_def(def_)


def test_builtin_defs_exist():
    """Test that built-in definitions exist and are valid."""
    # Test that we can load known builtin configs
    mdast_def = get_builtin_def("mdast")
    assert "attributes" in mdast_def
    assert "label" in mdast_def["attributes"]
    json_def = get_builtin_def("json")
    assert "attributes" in json_def
    assert "label" in json_def["attributes"]


def test_get_builtin_def():
    """Test getting built-in definition."""
    def_ = get_builtin_def("json")

    assert "attributes" in def_
    assert "type_overrides" in def_
    assert "ignore_types" in def_
    # Note: icon_map is no longer in definitions - icons come from const.py and are merged in adapter


def test_get_builtin_def_unknown():
    """Test error when requesting unknown built-in definition."""
    with pytest.raises(
        ConversionError, match="Failed to load def_ file 'unknown.json'"
    ):
        get_builtin_def("unknown")
