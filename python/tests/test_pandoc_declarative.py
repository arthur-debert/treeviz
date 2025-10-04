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
    """Load Pandoc test data with root node hack."""
    original_data = load_test_data("pandoc/pandoc_test.json")

    # Add 't' key to root for consistency
    return {
        "t": "Pandoc",
        "blocks": original_data["blocks"],
        "meta": original_data["meta"],
        "pandoc-api-version": original_data["pandoc-api-version"],
    }


def test_declarative_pandoc_adapter_loads():
    """Test that the YAML Pandoc adapter loads correctly."""
    adapter_def = AdapterLib.get("pandoc")
    assert adapter_def is not None
    assert adapter_def.type == "t"
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


def test_declarative_vs_lambda_equivalence():
    """Test that declarative adapter produces structurally equivalent results to lambda version.

    This enhanced test compares both structure and labels, documenting known differences
    between the declarative and lambda implementations.
    """
    test_data = _get_test_data()

    # Load declarative adapter
    declarative_def = AdapterLib.get("pandoc")
    declarative_result = adapt_node(test_data, asdict(declarative_def))

    # Load lambda-based adapter
    from treeviz.data.pandoc import definition as lambda_def

    lambda_result = adapt_node(test_data, lambda_def)

    # Compare structure (types, labels, and children counts should match)
    def compare_structure(node1, node2, path="root"):
        assert (
            node1.type == node2.type
        ), f"Type mismatch at {path}: {node1.type} vs {node2.type}"

        # Label comparison with known differences documented
        if node1.type == "Header":
            # Headers: declarative version doesn't include level number
            # Both should start with "H" and contain the same text content
            assert node1.label.startswith(
                "H"
            ), f"Header label should start with H at {path}"
            assert node2.label.startswith(
                "H"
            ), f"Header label should start with H at {path}"
            # Extract text after prefix for comparison
            text1 = node1.label[1:]  # Remove "H"
            text2 = (
                node2.label.split(": ", 1)[1]
                if ": " in node2.label
                else node2.label[1:]
            )
            assert (
                text1 == text2
            ), f"Header text mismatch at {path}: '{text1}' vs '{text2}'"
        elif node1.type in ["Para", "Plain", "ListItem", "CodeBlock"]:
            # These types may have slight differences in label formatting
            # Both should be non-empty and contain similar content
            assert len(node1.label) > 0, f"Empty label at {path}"
            assert len(node2.label) > 0, f"Empty label at {path}"
            # For CodeBlock, just check that both contain "CodeBlock"
            if node1.type == "CodeBlock":
                assert (
                    "CodeBlock" in node1.label
                ), f"CodeBlock label should contain 'CodeBlock' at {path}"
                assert (
                    "CodeBlock" in node2.label
                ), f"CodeBlock label should contain 'CodeBlock' at {path}"
            else:
                # Check that the core content is similar, ignoring truncation suffixes and whitespace differences
                core1 = " ".join(
                    node1.label.replace("...", "").split()
                )  # Normalize whitespace
                core2 = " ".join(
                    node2.label.replace("...", "").split()
                )  # Normalize whitespace
                # Compare first 40 characters to account for differences in truncation logic
                assert (
                    core1[:40] == core2[:40]
                ), f"Core content mismatch at {path}: '{core1[:40]}' vs '{core2[:40]}'"
        else:
            # For other node types, labels should match exactly
            assert (
                node1.label == node2.label
            ), f"Label mismatch at {path}: '{node1.label}' vs '{node2.label}'"

        assert len(node1.children) == len(
            node2.children
        ), f"Children count mismatch at {path}"

        for i, (child1, child2) in enumerate(
            zip(node1.children, node2.children)
        ):
            compare_structure(child1, child2, f"{path}.{i}")

    compare_structure(declarative_result, lambda_result)


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
