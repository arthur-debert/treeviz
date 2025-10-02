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
    create_sample_config,
    save_sample_config,
    get_builtin_config,
    BUILTIN_CONFIGS,
    ConversionError,
)


def test_load_config_from_dict():
    """Test loading configuration from dictionary."""
    config_dict = {"attributes": {"label": "name", "type": "node_type"}}

    result = load_config(config_dict=config_dict)
    assert result == config_dict


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
        assert result == config_dict
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
    """Test error when neither config_path nor config_dict are provided."""
    with pytest.raises(ConversionError, match="Must specify either"):
        load_config()


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
    config = create_sample_config()

    assert "attributes" in config
    assert "label" in config["attributes"]
    assert "icon_map" in config
    assert "type_overrides" in config
    assert "ignore_types" in config

    # Should be valid
    validate_config(config)


def test_save_sample_config():
    """Test saving sample configuration to file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        temp_path = f.name

    try:
        save_sample_config(temp_path)

        # Load and verify
        with open(temp_path, "r") as f:
            loaded_config = json.load(f)

        expected_config = create_sample_config()
        assert loaded_config == expected_config

    finally:
        Path(temp_path).unlink()


def test_builtin_configs_exist():
    """Test that built-in configurations exist and are valid."""
    assert "mdast" in BUILTIN_CONFIGS
    assert "json" in BUILTIN_CONFIGS

    # Each should be valid
    for format_name, config in BUILTIN_CONFIGS.items():
        # Note: Built-in configs may have callable values which validate_config doesn't handle
        # So we just check basic structure
        assert "attributes" in config
        assert "label" in config["attributes"]


def test_get_builtin_config():
    """Test getting built-in configuration."""
    config = get_builtin_config("json")

    assert "attributes" in config
    assert callable(
        config["attributes"]["label"]
    )  # Should be a lambda for JSON

    # Should be a copy, not the original
    config["test"] = "modified"
    assert "test" not in BUILTIN_CONFIGS["json"]


def test_get_builtin_config_unknown():
    """Test error when requesting unknown built-in configuration."""
    with pytest.raises(ConversionError, match="Unknown format 'unknown'"):
        get_builtin_config("unknown")
