"""
Test the new declarative Pandoc adapter using YAML definition.

This validates that the complex Pandoc AST can be processed entirely
using declarative patterns without lambda functions.
"""

from dataclasses import asdict
from treeviz.adapters import adapt_node
from treeviz.definitions import AdapterLib
from .conftest import load_test_data


def _get_test_data():
    """Load raw Pandoc test data - no modifications needed for declarative adapter."""
    # The declarative adapter should handle the raw pandoc JSON format directly
    return load_test_data("pandoc/pandoc_test.json")


def test_declarative_pandoc_adapter_loads():
    """Test that the YAML Pandoc adapter loads correctly."""
    adapter_def = AdapterLib.get("pandoc")
    assert adapter_def is not None
    assert adapter_def.type == {"path": "t", "default": "Unknown"}
    assert adapter_def.children == "c"


def test_declarative_pandoc_basic_conversion():
    """Test basic AST conversion with declarative adapter."""
    test_data = _get_test_data()
    adapter_def = AdapterLib.get("pandoc")

    result = adapt_node(test_data, asdict(adapter_def))

    assert result is not None
    assert result.type == "Pandoc"
    assert result.label == "Pandoc Document"
    assert len(result.children) > 0


def test_declarative_header_processing():
    """Test header processing with transform pipelines."""
    # Simple header node
    header_node = {
        "t": "Header",
        "c": [
            1,
            ["header-id"],
            [
                {"t": "Str", "c": "Test"},
                {"t": "Space"},
                {"t": "Str", "c": "Header"},
            ],
        ],
    }

    adapter_def = AdapterLib.get("pandoc")
    result = adapt_node(header_node, asdict(adapter_def))

    assert result.type == "Header"
    assert "Test Header" in result.label
    assert result.label.startswith("H")


def test_declarative_bullet_list_mapping():
    """Test bullet list collection mapping."""
    bullet_list = {
        "t": "BulletList",
        "c": [
            [{"t": "Plain", "c": [{"t": "Str", "c": "Item 1"}]}],
            [{"t": "Plain", "c": [{"t": "Str", "c": "Item 2"}]}],
        ],
    }

    adapter_def = AdapterLib.get("pandoc")
    result = adapt_node(bullet_list, asdict(adapter_def))

    assert result.type == "BulletList"
    assert result.label == "Bullet List"
    assert len(result.children) == 2

    # Check that synthetic ListItem nodes were created
    for child in result.children:
        assert child.type == "ListItem"


def test_complex_nested_processing():
    """Test complex nested content processing."""
    complex_node = {
        "t": "Para",
        "c": [
            {"t": "Str", "c": "This"},
            {"t": "Space"},
            {"t": "Strong", "c": [{"t": "Str", "c": "bold"}]},
            {"t": "Space"},
            {"t": "Str", "c": "text"},
            {"t": "SoftBreak"},
            {"t": "Str", "c": "continues"},
        ],
    }

    adapter_def = AdapterLib.get("pandoc")
    result = adapt_node(complex_node, asdict(adapter_def))

    assert result.type == "Para"
    # Should extract and join text from Str nodes
    assert "This" in result.label
    assert "text" in result.label
    assert "continues" in result.label
