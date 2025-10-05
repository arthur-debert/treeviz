"""
Integration tests for the MediaWiki declarative adapter.
"""

from treeviz.adapters import adapt_node
from treeviz.definitions import AdapterLib
from .conftest import load_test_data


def _flatten_nodes(node):
    """Flatten tree into a list of all nodes."""
    nodes = [node]
    if node and node.children:
        for child in node.children:
            nodes.extend(_flatten_nodes(child))
    return nodes


def test_mediawiki_adapter_integration():
    """Test that the mediawiki adapter correctly transforms a complex AST."""
    test_data = load_test_data("mediawiki/complex4.json")
    mediawiki_adapter = AdapterLib.get("mediawiki")

    # Adapt the data using the mediawiki adapter
    result = adapt_node(test_data, mediawiki_adapter)

    # Verify the root node
    assert result is not None, "Adaptation should not result in None"
    assert result.type == "Wikicode"
    assert result.label == "MediaWiki Document"
    assert len(result.children) > 0

    # Flatten the tree to inspect all nodes
    all_nodes = _flatten_nodes(result)
    node_types = {n.type for n in all_nodes}

    # Check for expected node types
    expected_types = {
        "Wikicode",
        "Heading",
        "Text",
        "Tag",
        "Wikilink",
    }
    assert expected_types.issubset(node_types)

    # Check for specific content
    labels = {n.label for n in all_nodes}
    assert "H1: Comprehensive Example" in labels
    assert "H2: Nested Lists" in labels
    assert any("bold and italic" in node.label for node in all_nodes)
    assert any("strikethrough" in node.label for node in all_nodes)


def test_mediawiki_template_handling():
    """Test that Template and Parameter nodes are handled correctly."""
    test_data = load_test_data("mediawiki/complex3.json")
    mediawiki_adapter = AdapterLib.get("mediawiki")

    # Adapt the data
    result = adapt_node(test_data, mediawiki_adapter)
    assert result is not None

    # Find a Template node and check its children
    all_nodes = _flatten_nodes(result)
    templates = [n for n in all_nodes if n.type == "Template"]
    assert len(templates) > 0, "No Template nodes found"
    assert templates[0].label == "{{ Infobox }}"

    # Check for Parameter children
    param_children = [
        child for child in templates[0].children if child.type == "Parameter"
    ]
    assert len(param_children) > 0, "No Parameter children found in Template"
    assert "name = ..." in param_children[0].label
    assert "data = ..." in param_children[1].label
    assert "status = ..." in param_children[2].label