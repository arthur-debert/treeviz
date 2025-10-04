"""
Test the type override system to ensure it can properly change node types.

This test addresses a bug where type overrides only change extraction patterns
but don't actually change the resulting node's type field.
"""

from treeviz.adapters import adapt_node


def test_type_override_changes_node_type():
    """Test that type overrides can actually change the resulting node's type."""
    # Define a simple adapter that maps "Unknown" to "Document"
    adapter_def = {
        "type": {"path": "t", "default": "Unknown"},
        "children": "children",
        "label": "label",
        "type_overrides": {
            "Unknown": {
                "type": "Document",  # This should change the node type
                "label": "Root Document",
            }
        },
    }

    # Test data without 't' field (should trigger Unknown default)
    test_data = {"label": "Test Node", "children": []}

    result = adapt_node(test_data, adapter_def)

    # The bug: currently this fails because result.type is "Unknown" not "Document"
    assert (
        result.type == "Document"
    ), f"Expected type 'Document', got '{result.type}'"
    assert result.label == "Root Document"


def test_type_override_with_explicit_type():
    """Test that type overrides work when the original type is explicitly set."""
    adapter_def = {
        "type": "nodeType",
        "children": "children",
        "label": "label",
        "type_overrides": {
            "OldType": {"type": "NewType", "label": "Converted Node"}
        },
    }

    test_data = {"nodeType": "OldType", "label": "Original", "children": []}

    result = adapt_node(test_data, adapter_def)

    # This should work if type overrides actually change the type
    assert (
        result.type == "NewType"
    ), f"Expected type 'NewType', got '{result.type}'"
    assert result.label == "Converted Node"


def test_type_override_preserves_other_fields():
    """Test that type overrides preserve fields that aren't overridden."""
    adapter_def = {
        "type": "t",
        "children": "children",
        "label": "label",
        "icon": "icon",
        "type_overrides": {
            "TestType": {
                "type": "OverriddenType",
                # Don't override label or icon - they should be preserved
            }
        },
    }

    test_data = {
        "t": "TestType",
        "label": "Original Label",
        "icon": "🔥",
        "children": [],
    }

    result = adapt_node(test_data, adapter_def)

    assert result.type == "OverriddenType"
    assert result.label == "Original Label"  # Should preserve original
    assert result.icon == "🔥"  # Should preserve original


def test_pandoc_root_document_scenario():
    """Test the specific Pandoc scenario: native AST root with no 't' field."""
    # This mimics the actual pandoc adapter configuration
    adapter_def = {
        "type": {"path": "t", "default": "Unknown"},
        "children": "c",
        "label": "t",
        "type_overrides": {
            "Unknown": {
                "type": "Pandoc",
                "children": "blocks",
                "label": "Pandoc Document",
            }
        },
    }

    # Raw pandoc root structure (no 't' field)
    pandoc_root = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [{"t": "Header", "c": [1, [], [{"t": "Str", "c": "Title"}]]}],
    }

    result = adapt_node(pandoc_root, adapter_def)

    # This is the key test - should work with native AST
    assert (
        result.type == "Pandoc"
    ), f"Expected type 'Pandoc', got '{result.type}'"
    assert result.label == "Pandoc Document"
    assert len(result.children) > 0  # Should have processed blocks
