"""
Tests for the Renderer.
"""


from treeviz.renderer import Renderer


def test_render_simple_tree(sample_node_tree):
    """
    Test rendering a simple Node tree.
    """
    renderer = Renderer()
    output = renderer.render(sample_node_tree)

    # Split the output into lines for easier comparison
    lines = output.split("\n")

    assert "⧉ Document" in lines[0]
    assert "¶ This is a paragraph." in lines[1]
    assert "☰ List" in lines[2]
    assert "• Item 1" in lines[3]
    assert "• Item 2" in lines[4]


def test_render_with_custom_symbols(sample_node_tree):
    """
    Test rendering with custom symbols.
    """
    custom_symbols = {
        "document": "[D]",
        "paragraph": "[P]",
        "list": "[L]",
        "listItem": "[I]",
    }
    renderer = Renderer(symbols=custom_symbols)
    output = renderer.render(sample_node_tree)

    lines = output.split("\n")

    assert "[D] Document" in lines[0]
    assert "[P] This is a paragraph." in lines[1]
    assert "[L] List" in lines[2]
    assert "[I] Item 1" in lines[3]
    assert "[I] Item 2" in lines[4]
