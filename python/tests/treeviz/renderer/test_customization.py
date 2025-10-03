"""
Tests for Renderer customization features.

This test file focuses on symbol customization, terminal width handling,
and other renderer definition options.
"""

from treeviz.renderer import render, create_render_options, DEFAULT_SYMBOLS
from treeviz.model import Node


def test_default_symbols():
    """Test that default symbols are properly defined."""
    options = create_render_options()

    # Test some key default symbols
    assert options.symbols["document"] == "⧉"
    assert options.symbols["paragraph"] == "¶"
    assert options.symbols["list"] == "☰"
    assert options.symbols["text"] == "◦"
    assert options.symbols["unknown"] == "?"


def test_custom_symbol_mapping():
    """Test rendering with custom symbol mapping."""
    custom_symbols = {
        "document": "[DOC]",
        "paragraph": "[P]",
        "list": "[LIST]",
        "text": "[T]",
    }

    node = Node(type="document", label="Document")
    options = create_render_options(symbols=custom_symbols)

    output = render(node, options)
    assert "[DOC] Document" in output


def test_partial_symbol_override():
    """Test that partial symbol override preserves defaults."""
    partial_symbols = {"document": "📄", "paragraph": "📝"}

    options = create_render_options(symbols=partial_symbols)

    # Custom symbols should be used
    assert options.symbols["document"] == "📄"
    assert options.symbols["paragraph"] == "📝"

    # Default symbols should be preserved
    assert options.symbols["text"] == "◦"
    assert options.symbols["list"] == "☰"


def test_custom_symbols_in_tree():
    """Test custom symbols in a complete tree structure."""
    custom_symbols = {
        "document": "[D]",
        "paragraph": "[P]",
        "list": "[L]",
        "listItem": "[I]",
        "text": "[T]",
    }

    children = [
        Node(type="paragraph", label="Paragraph"),
        Node(
            type="list",
            label="List",
            children=[
                Node(type="listItem", label="Item 1"),
                Node(type="listItem", label="Item 2"),
            ],
        ),
    ]
    root = Node(type="document", label="Document", children=children)

    options = create_render_options(symbols=custom_symbols)
    output = render(root, options)

    lines = output.split("\n")
    assert "[D] Document" in lines[0]
    assert "[P] Paragraph" in lines[1]
    assert "[L] List" in lines[2]
    assert "[I] Item 1" in lines[3]
    assert "[I] Item 2" in lines[4]


def test_empty_custom_symbols():
    """Test renderer with empty custom symbols dict."""
    options = create_render_options(symbols={})

    # Should still have all default symbols
    assert options.symbols == DEFAULT_SYMBOLS


def test_renderer_terminal_width():
    """Test renderer terminal width definition."""
    options_80 = create_render_options(terminal_width=80)
    options_120 = create_render_options(terminal_width=120)

    assert options_80.terminal_width == 80
    assert options_120.terminal_width == 120


def test_unicode_symbols():
    """Test rendering with Unicode symbols."""
    unicode_symbols = {
        "document": "📄",
        "paragraph": "📝",
        "list": "📋",
        "text": "💬",
        "heading": "📖",
        "code": "💻",
    }

    node = Node(type="document", label="Unicode Document")
    options = create_render_options(symbols=unicode_symbols)

    output = render(node, options)
    assert "📄 Unicode Document" in output


def test_multi_character_symbols():
    """Test rendering with multi-character symbols."""
    multi_char_symbols = {
        "document": "DOC:",
        "paragraph": "PARA:",
        "list": "LIST:",
        "text": "TEXT:",
    }

    children = [
        Node(type="paragraph", label="Paragraph"),
        Node(type="text", label="Text"),
    ]
    root = Node(type="document", label="Document", children=children)

    options = create_render_options(symbols=multi_char_symbols)
    output = render(root, options)

    lines = output.split("\n")
    assert "DOC: Document" in lines[0]
    assert "PARA: Paragraph" in lines[1]
    assert "TEXT: Text" in lines[2]


def test_symbol_override_precedence():
    """Test that custom symbols take precedence over defaults."""
    # Start with default options
    default_options = create_render_options()
    default_doc_symbol = default_options.symbols["document"]

    # Override with custom symbol
    custom_symbols = {"document": "CUSTOM"}
    custom_options = create_render_options(symbols=custom_symbols)

    assert custom_options.symbols["document"] == "CUSTOM"
    assert custom_options.symbols["document"] != default_doc_symbol


def test_none_symbols():
    """Test renderer behavior with None symbols parameter."""
    options = create_render_options(symbols=None)

    # Should use default symbols
    assert options.symbols == DEFAULT_SYMBOLS


def test_special_character_symbols():
    """Test rendering with special characters as symbols."""
    special_symbols = {
        "document": "→",
        "paragraph": "•",
        "list": "▸",
        "text": "◈",
        "heading": "▲",
    }

    node = Node(type="heading", label="Special Heading")
    options = create_render_options(symbols=special_symbols)

    output = render(node, options)
    assert "▲ Special Heading" in output


def test_symbol_consistency_across_renders():
    """Test that symbols remain consistent across multiple renders."""
    custom_symbols = {"document": "★", "text": "○"}
    options = create_render_options(symbols=custom_symbols)

    node1 = Node(type="document", label="Doc 1")
    node2 = Node(type="text", label="Text 1")

    output1 = render(node1, options)
    output2 = render(node2, options)

    assert "★ Doc 1" in output1
    assert "○ Text 1" in output2

    # Render again to ensure consistency
    output1_again = render(node1, options)
    assert output1 == output1_again


def test_renderer_immutability():
    """Test that render options don't change between renders."""
    options = create_render_options()
    original_symbols = options.symbols.copy()

    # Render some nodes
    node1 = Node(type="document", label="Document")
    node2 = Node(type="text", label="Text")

    render(node1, options)
    render(node2, options)

    # Symbols should remain unchanged
    assert options.symbols == original_symbols
