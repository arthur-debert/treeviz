"""
Tests for Renderer indentation and formatting behavior.

This test file focuses on proper indentation of nested structures,
spacing, and visual formatting of the rendered output.
"""

import pytest
from treeviz.renderer import Renderer
from treeviz.model import Node


def test_no_indentation_for_root():
    """Test that root node has no indentation."""
    node = Node(type="document", label="Root")
    renderer = Renderer()
    
    output = renderer.render(node)
    
    assert output.startswith("⧉ Root")
    assert not output.startswith(" ")


def test_single_level_indentation():
    """Test indentation for direct children."""
    child = Node(type="text", label="Child")
    parent = Node(type="document", label="Parent", children=[child])
    
    renderer = Renderer()
    output = renderer.render(parent)
    
    lines = output.split("\n")
    assert "⧉ Parent" in lines[0]
    assert "  ◦ Child" in lines[1]  # 2 spaces indentation


def test_multi_level_indentation():
    """Test indentation for deeply nested structures."""
    grandchild = Node(type="text", label="Grandchild")
    child = Node(type="paragraph", label="Child", children=[grandchild])
    root = Node(type="document", label="Root", children=[child])
    
    renderer = Renderer()
    output = renderer.render(root)
    
    lines = output.split("\n")
    assert "⧉ Root" in lines[0]
    assert "  ¶ Child" in lines[1]
    assert "    ◦ Grandchild" in lines[2]  # 4 spaces indentation


def test_consistent_indentation_width():
    """Test that indentation width is consistent."""
    # Create a 4-level deep tree
    level4 = Node(type="text", label="Level 4")
    level3 = Node(type="paragraph", label="Level 3", children=[level4])
    level2 = Node(type="paragraph", label="Level 2", children=[level3])
    level1 = Node(type="document", label="Level 1", children=[level2])
    
    renderer = Renderer()
    output = renderer.render(level1)
    
    lines = output.split("\n")
    assert "⧉ Level 1" in lines[0]           # 0 spaces
    assert "  ¶ Level 2" in lines[1]         # 2 spaces
    assert "    ¶ Level 3" in lines[2]       # 4 spaces  
    assert "      ◦ Level 4" in lines[3]     # 6 spaces


def test_sibling_indentation():
    """Test that siblings at same level have same indentation."""
    children = [
        Node(type="text", label="Sibling 1"),
        Node(type="text", label="Sibling 2"),
        Node(type="text", label="Sibling 3")
    ]
    parent = Node(type="document", label="Parent", children=children)
    
    renderer = Renderer()
    output = renderer.render(parent)
    
    lines = output.split("\n")
    assert "⧉ Parent" in lines[0]
    # All siblings should have same indentation
    assert "  ◦ Sibling 1" in lines[1]
    assert "  ◦ Sibling 2" in lines[2]
    assert "  ◦ Sibling 3" in lines[3]


def test_mixed_depth_siblings():
    """Test indentation when siblings have different depths."""
    # Create tree with varying depth siblings
    deep_grandchild = Node(type="text", label="Deep Grandchild")
    deep_child = Node(type="paragraph", label="Deep Child", children=[deep_grandchild])
    shallow_child = Node(type="text", label="Shallow Child")
    
    root = Node(type="document", label="Root", children=[deep_child, shallow_child])
    
    renderer = Renderer()
    output = renderer.render(root)
    
    lines = output.split("\n")
    assert "⧉ Root" in lines[0]
    assert "  ¶ Deep Child" in lines[1]
    assert "    ◦ Deep Grandchild" in lines[2]
    assert "  ◦ Shallow Child" in lines[3]  # Back to level 1 indentation


def test_complex_tree_indentation():
    """Test indentation in a complex tree structure."""
    # Build a more complex tree:
    #   Document
    #     Heading
    #     Paragraph
    #       Text 1
    #       Text 2
    #     List
    #       Item 1
    #         Sub Item
    #       Item 2
    
    sub_item = Node(type="text", label="Sub Item")
    item1 = Node(type="listItem", label="Item 1", children=[sub_item])
    item2 = Node(type="listItem", label="Item 2")
    
    text1 = Node(type="text", label="Text 1")
    text2 = Node(type="text", label="Text 2")
    
    heading = Node(type="heading", label="Heading")
    paragraph = Node(type="paragraph", label="Paragraph", children=[text1, text2])
    list_node = Node(type="list", label="List", children=[item1, item2])
    
    document = Node(type="document", label="Document", children=[heading, paragraph, list_node])
    
    renderer = Renderer()
    output = renderer.render(document)
    
    expected_patterns = [
        "⧉ Document",           # 0 spaces
        "  ⊤ Heading",          # 2 spaces
        "  ¶ Paragraph",        # 2 spaces
        "    ◦ Text 1",         # 4 spaces
        "    ◦ Text 2",         # 4 spaces
        "  ☰ List",             # 2 spaces
        "    • Item 1",         # 4 spaces
        "      ◦ Sub Item",     # 6 spaces
        "    • Item 2"          # 4 spaces
    ]
    
    lines = output.split("\n")
    assert len(lines) == len(expected_patterns)
    for i, pattern in enumerate(expected_patterns):
        assert pattern in lines[i], f"Expected '{pattern}' in line {i}: '{lines[i]}'"


def test_empty_children_no_extra_lines():
    """Test that nodes with empty children don't create extra lines."""
    empty_child = Node(type="paragraph", label="Empty", children=[])
    parent = Node(type="document", label="Parent", children=[empty_child])
    
    renderer = Renderer()
    output = renderer.render(parent)
    
    lines = output.split("\n")
    assert len(lines) == 2
    assert "⧉ Parent" in lines[0]
    assert "  ¶ Empty" in lines[1]


def test_indentation_with_long_labels():
    """Test that indentation works correctly with long labels."""
    long_label = "This is a very long label that might affect indentation behavior"
    child = Node(type="text", label=long_label)
    parent = Node(type="document", label="Short", children=[child])
    
    renderer = Renderer()
    output = renderer.render(parent)
    
    lines = output.split("\n")
    assert "⧉ Short" in lines[0]
    # Child should be indented correctly despite long label
    assert lines[1].startswith("  ◦ ")
    # Long labels may be truncated, so check for the beginning
    assert "This is a very long" in lines[1]
    assert lines[1].startswith("  ")  # Still proper indentation


def test_indentation_preserves_spaces_in_labels():
    """Test that label spaces are preserved within indented lines."""
    child = Node(type="text", label="Label with  multiple   spaces")
    parent = Node(type="document", label="Parent", children=[child])
    
    renderer = Renderer()
    output = renderer.render(parent)
    
    lines = output.split("\n")
    assert "Label with  multiple   spaces" in lines[1]
    assert lines[1].startswith("  ◦ ")


def test_maximum_depth_indentation():
    """Test indentation behavior at very deep nesting levels."""
    # Create 10-level deep tree
    current = Node(type="text", label="Level 10")
    
    for i in range(9, 0, -1):
        current = Node(type="paragraph", label=f"Level {i}", children=[current])
    
    renderer = Renderer()
    output = renderer.render(current)
    
    lines = output.split("\n")
    
    # Check that each level has correct indentation
    for i, line in enumerate(lines):
        expected_spaces = i * 2
        actual_spaces = len(line) - len(line.lstrip())
        assert actual_spaces == expected_spaces, f"Line {i} should have {expected_spaces} spaces, got {actual_spaces}"