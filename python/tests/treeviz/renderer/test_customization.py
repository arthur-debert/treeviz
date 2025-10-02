"""
Tests for Renderer customization features.

This test file focuses on symbol customization, terminal width handling,
and other renderer configuration options.
"""

import pytest
from treeviz.renderer import Renderer, DEFAULT_SYMBOLS
from treeviz.model import Node


def test_default_symbols():
    """Test that default symbols are properly defined."""
    renderer = Renderer()
    
    # Test some key default symbols
    assert renderer.symbols["document"] == "⧉"
    assert renderer.symbols["paragraph"] == "¶"
    assert renderer.symbols["list"] == "☰"
    assert renderer.symbols["text"] == "◦"
    assert renderer.symbols["unknown"] == "?"


def test_custom_symbol_mapping():
    """Test rendering with custom symbol mapping."""
    custom_symbols = {
        "document": "[DOC]",
        "paragraph": "[P]",
        "list": "[LIST]",
        "text": "[T]",
    }
    
    node = Node(type="document", label="Document")
    renderer = Renderer(symbols=custom_symbols)
    
    output = renderer.render(node)
    assert "[DOC] Document" in output


def test_partial_symbol_override():
    """Test that partial symbol override preserves defaults."""
    partial_symbols = {
        "document": "📄",
        "paragraph": "📝"
    }
    
    renderer = Renderer(symbols=partial_symbols)
    
    # Custom symbols should be used
    assert renderer.symbols["document"] == "📄"
    assert renderer.symbols["paragraph"] == "📝"
    
    # Default symbols should be preserved
    assert renderer.symbols["text"] == "◦"
    assert renderer.symbols["list"] == "☰"


def test_custom_symbols_in_tree():
    """Test custom symbols in a complete tree structure."""
    custom_symbols = {
        "document": "[D]",
        "paragraph": "[P]", 
        "list": "[L]",
        "listItem": "[I]",
        "text": "[T]"
    }
    
    children = [
        Node(type="paragraph", label="Paragraph"),
        Node(type="list", label="List", children=[
            Node(type="listItem", label="Item 1"),
            Node(type="listItem", label="Item 2")
        ])
    ]
    root = Node(type="document", label="Document", children=children)
    
    renderer = Renderer(symbols=custom_symbols)
    output = renderer.render(root)
    
    lines = output.split("\n")
    assert "[D] Document" in lines[0]
    assert "[P] Paragraph" in lines[1]
    assert "[L] List" in lines[2]
    assert "[I] Item 1" in lines[3]
    assert "[I] Item 2" in lines[4]


def test_empty_custom_symbols():
    """Test renderer with empty custom symbols dict."""
    renderer = Renderer(symbols={})
    
    # Should still have all default symbols
    assert renderer.symbols == DEFAULT_SYMBOLS


def test_renderer_terminal_width():
    """Test renderer terminal width configuration."""
    renderer_80 = Renderer(terminal_width=80)
    renderer_120 = Renderer(terminal_width=120)
    
    assert renderer_80.terminal_width == 80
    assert renderer_120.terminal_width == 120


def test_unicode_symbols():
    """Test rendering with Unicode symbols."""
    unicode_symbols = {
        "document": "📄",
        "paragraph": "📝", 
        "list": "📋",
        "text": "💬",
        "heading": "📖",
        "code": "💻"
    }
    
    node = Node(type="document", label="Unicode Document")
    renderer = Renderer(symbols=unicode_symbols)
    
    output = renderer.render(node)
    assert "📄 Unicode Document" in output


def test_multi_character_symbols():
    """Test rendering with multi-character symbols."""
    multi_char_symbols = {
        "document": "DOC:",
        "paragraph": "PARA:",
        "list": "LIST:",
        "text": "TEXT:"
    }
    
    children = [
        Node(type="paragraph", label="Paragraph"),
        Node(type="text", label="Text")
    ]
    root = Node(type="document", label="Document", children=children)
    
    renderer = Renderer(symbols=multi_char_symbols)
    output = renderer.render(root)
    
    lines = output.split("\n")
    assert "DOC: Document" in lines[0]
    assert "PARA: Paragraph" in lines[1]
    assert "TEXT: Text" in lines[2]


def test_symbol_override_precedence():
    """Test that custom symbols take precedence over defaults."""
    # Start with default renderer
    default_renderer = Renderer()
    default_doc_symbol = default_renderer.symbols["document"]
    
    # Override with custom symbol
    custom_symbols = {"document": "CUSTOM"}
    custom_renderer = Renderer(symbols=custom_symbols)
    
    assert custom_renderer.symbols["document"] == "CUSTOM"
    assert custom_renderer.symbols["document"] != default_doc_symbol


def test_none_symbols():
    """Test renderer behavior with None symbols parameter."""
    renderer = Renderer(symbols=None)
    
    # Should use default symbols
    assert renderer.symbols == DEFAULT_SYMBOLS


def test_special_character_symbols():
    """Test rendering with special characters as symbols."""
    special_symbols = {
        "document": "→",
        "paragraph": "•",
        "list": "▸",
        "text": "◈",
        "heading": "▲"
    }
    
    node = Node(type="heading", label="Special Heading")
    renderer = Renderer(symbols=special_symbols)
    
    output = renderer.render(node)
    assert "▲ Special Heading" in output


def test_symbol_consistency_across_renders():
    """Test that symbols remain consistent across multiple renders."""
    custom_symbols = {"document": "★", "text": "○"}
    renderer = Renderer(symbols=custom_symbols)
    
    node1 = Node(type="document", label="Doc 1")
    node2 = Node(type="text", label="Text 1")
    
    output1 = renderer.render(node1)
    output2 = renderer.render(node2)
    
    assert "★ Doc 1" in output1
    assert "○ Text 1" in output2
    
    # Render again to ensure consistency
    output1_again = renderer.render(node1)
    assert output1 == output1_again


def test_renderer_immutability():
    """Test that renderer state doesn't change between renders."""
    renderer = Renderer()
    original_symbols = renderer.symbols.copy()
    
    # Render some nodes
    node1 = Node(type="document", label="Document")
    node2 = Node(type="text", label="Text")
    
    renderer.render(node1)
    renderer.render(node2)
    
    # Symbols should remain unchanged
    assert renderer.symbols == original_symbols