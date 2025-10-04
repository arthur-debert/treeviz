"""
Main treeviz public API module.

This module provides the primary public interface for the treeviz library,
including the polymorphic render() function and core classes.
"""

from .definitions.model import AdapterDef  # noqa: F401
from .definitions.lib.lib import Lib as AdapterLib  # noqa: F401
from .__main__ import generate_viz


# Output format constants for better UX
OUTPUT_TEXT = "text"  # Plain text output
OUTPUT_TERM = "term"  # Terminal output with colors/formatting
OUTPUT_JSON = "json"  # JSON representation
OUTPUT_YAML = "yaml"  # YAML representation
OUTPUT_OBJ = "obj"  # Return Node tree object


def render(ast, adapter="3viz", output="text"):
    """
    Render any AST with treeviz visualization.

    Thin wrapper around generate_viz that provides the expected API signature.

    Args:
        ast: File path, stdin ("-"), or Python object (dict/list/Node)
        adapter: Adapter name ("3viz", "mdast", "unist") or Adapter/dict object
        output: Output format - "text", "term", "json", "yaml", or "obj"

    Returns:
        String output or Node object (if output="obj")
    """
    return generate_viz(
        document_path=ast, adapter_spec=adapter, output_format=output
    )
