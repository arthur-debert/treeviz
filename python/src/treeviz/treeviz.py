"""
Main treeviz public API module.

This module provides the primary public interface for the treeviz library,
including the polymorphic render() function and core classes.
"""

from .definitions.model import AdapterDef  # noqa: F401
from .definitions.lib import AdapterLib  # noqa: F401
from .__main__ import generate_viz


# Output format constants for better UX
OUTPUT_TEXT = "text"  # Plain text output
OUTPUT_TERM = "term"  # Terminal output with colors/formatting
OUTPUT_JSON = "json"  # JSON representation
OUTPUT_YAML = "yaml"  # YAML representation
OUTPUT_OBJ = "obj"  # Return Node tree object


def render(ast, adapter="3viz", output="text", style=None, theme=None):
    """
    Render any AST with treeviz visualization.

    Thin wrapper around generate_viz that provides the expected API signature.

    Args:
        ast: File path, stdin ("-"), or Python object (dict/list/Node)
        adapter: Adapter name ("3viz", "mdast", "unist") or Adapter/dict object
        output: Output format - "text", "term", "json", "yaml", or "obj"
        style: Optional - RenderingOptions object, dict config, or path to style.yaml
        theme: Optional - Theme name override (e.g., "dark", "light", "minimal")

    Returns:
        String output or Node object (if output="obj")
    """
    # Convert style to appropriate format for generate_viz
    style_path = None
    if style is not None:
        from pathlib import Path
        from .rendering import RenderingOptions

        if isinstance(style, (str, Path)):
            # Path to style file
            style_path = style
        elif isinstance(style, RenderingOptions):
            # TODO: In the future, we could serialize and pass the options
            # For now, generate_viz only accepts file paths
            pass
        elif isinstance(style, dict):
            # TODO: Could create a temporary file or enhance generate_viz
            pass

    return generate_viz(
        document_path=ast,
        adapter_spec=adapter,
        output_format=output,
        style=style_path,
        theme=theme,
    )
