"""
Tests for configuration management.
"""

import json
import tempfile
import pytest
from pathlib import Path

from treeviz.config import (
    load_config,
    validate_config,
    get_builtin_config,
    _load_config_file,
    ConversionError,
)


def test_load_config_from_dict():
    """Test loading configuration from dictionary."""
    config_dict = {"attributes": {"label": "name", "type": "node_type"}}

    result = load_config(config_dict=config_dict)
    
    # Check that user config was merged with defaults
    assert result["attributes"]["label"] == "name"  # User override
    assert result["attributes"]["type"] == "node_type"  # User override
    assert result["attributes"]["children"] == "children"  # Default
    assert "icon_map" in result  # Default included
    assert "type_overrides" in result  # Default included
    assert "ignore_types" in result  # Default included


def test_load_config_from_file():
    """Test loading configuration from JSON file."""
    config_dict = {
        "attributes": {"label": "name", "type": "node_type"},
        "icon_map": {"test": "⧉"},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(config_dict, f)
        temp_path = f.name

    try:
        result = load_config(config_path=temp_path)
        
        # Check that user config was merged with defaults
        assert result["attributes"]["label"] == "name"  # User override
        assert result["attributes"]["type"] == "node_type"  # User override
        assert result["attributes"]["children"] == "children"  # Default
        assert result["icon_map"]["test"] == "⧉"  # User override
        assert "document" in result["icon_map"]  # Default icons included
        assert "type_overrides" in result  # Default included
        assert "ignore_types" in result  # Default included
    finally:
        Path(temp_path).unlink()


def test_load_config_file_not_found():
    """Test error when configuration file doesn't exist."""
    with pytest.raises(ConversionError, match="Configuration file not found"):
        load_config(config_path="/nonexistent/path.json")


def test_load_config_invalid_json():
    """Test error when configuration file has invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(ConversionError, match="Invalid JSON"):
            load_config(config_path=temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_config_both_sources():
    """Test error when both config_path and config_dict are provided."""
    with pytest.raises(ConversionError, match="Cannot specify both"):
        load_config(
            config_path="test.json",
            config_dict={"attributes": {"label": "name"}},
        )


def test_load_config_no_sources():
    """Test that default configuration is returned when no sources are provided."""
    result = load_config()
    
    # Should return default configuration
    assert "attributes" in result
    assert "icon_map" in result
    assert "type_overrides" in result
    assert "ignore_types" in result
    
    # Check that we got the expected defaults
    assert result["attributes"]["label"] == "label"
    assert result["attributes"]["type"] == "type"
    assert result["attributes"]["children"] == "children"


def test_validate_config_valid():
    """Test validation of valid configuration."""
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes",
        },
        "icon_map": {"test": "⧉"},
        "type_overrides": {"text": {"label": "content"}},
        "ignore_types": ["comment"],
    }

    result = validate_config(config)
    assert result == config


def test_validate_config_not_dict():
    """Test validation error when config is not a dictionary."""
    with pytest.raises(ConversionError, match="must be a dictionary"):
        validate_config("not a dict")


def test_validate_config_missing_attributes():
    """Test validation error when attributes section is missing."""
    with pytest.raises(ConversionError, match="must include 'attributes'"):
        validate_config({})


def test_validate_config_attributes_not_dict():
    """Test validation error when attributes is not a dictionary."""
    with pytest.raises(
        ConversionError, match="'attributes' section must be a dictionary"
    ):
        validate_config({"attributes": "not a dict"})


def test_validate_config_missing_label():
    """Test validation error when label extraction is not specified."""
    with pytest.raises(
        ConversionError, match="must specify how to extract 'label'"
    ):
        validate_config({"attributes": {"type": "node_type"}})


def test_validate_config_invalid_icon_map():
    """Test validation error when icon_map is not a dictionary."""
    config = {"attributes": {"label": "name"}, "icon_map": "not a dict"}

    with pytest.raises(
        ConversionError, match="'icon_map' must be a dictionary"
    ):
        validate_config(config)


def test_validate_config_invalid_type_overrides():
    """Test validation error when type_overrides is not a dictionary."""
    config = {"attributes": {"label": "name"}, "type_overrides": "not a dict"}

    with pytest.raises(
        ConversionError, match="'type_overrides' must be a dictionary"
    ):
        validate_config(config)


def test_validate_config_invalid_ignore_types():
    """Test validation error when ignore_types is not a list."""
    config = {"attributes": {"label": "name"}, "ignore_types": "not a list"}

    with pytest.raises(ConversionError, match="'ignore_types' must be a list"):
        validate_config(config)


def test_validate_config_invalid_type_override_value():
    """Test validation error when type override value is not a dictionary."""
    config = {
        "attributes": {"label": "name"},
        "type_overrides": {"text": "not a dict"},
    }

    with pytest.raises(
        ConversionError, match="Type override for 'text' must be a dictionary"
    ):
        validate_config(config)


def test_create_sample_config():
    """Test creation of sample configuration."""
    config = _load_config_file('sample.json')

    assert "attributes" in config
    assert "label" in config["attributes"]
    assert "icon_map" in config
    assert "type_overrides" in config
    assert "ignore_types" in config

    # Should be valid
    validate_config(config)



def test_builtin_configs_exist():
    """Test that built-in configurations exist and are valid."""
    # Test that we can load known builtin configs
    mdast_config = get_builtin_config("mdast")
    assert "attributes" in mdast_config
    assert "label" in mdast_config["attributes"]
    
    json_config = get_builtin_config("json")
    assert "attributes" in json_config
    assert "label" in json_config["attributes"]


def test_get_builtin_config():
    """Test getting built-in configuration."""
    config = get_builtin_config("json")

    assert "attributes" in config
    assert "icon_map" in config
    assert "type_overrides" in config
    assert "ignore_types" in config
    
    # Should load from JSON file with simple string mappings
    assert config["attributes"]["label"] == "type"
    assert config["icon_map"]["dict"] == "{}"
    
    # Should include default config elements
    assert "document" in config["icon_map"]  # From defaults


def test_get_builtin_config_unknown():
    """Test error when requesting unknown built-in configuration."""
    with pytest.raises(ConversionError, match="Failed to load config file 'unknown.json'"):
        get_builtin_config("unknown")
