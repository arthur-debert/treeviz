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


def render(ast, adapter="3viz", output="text", presentation=None):
    """
    Render any AST with treeviz visualization.

    Thin wrapper around generate_viz that provides the expected API signature.

    Args:
        ast: File path, stdin ("-"), or Python object (dict/list/Node)
        adapter: Adapter name ("3viz", "mdast", "unist") or Adapter/dict object
        output: Output format - "text", "term", "json", "yaml", or "obj"
        presentation: Optional - Presentation object, dict config, or path to presentation.yaml

    Returns:
        String output or Node object (if output="obj")
    """
    # Convert presentation to appropriate format for generate_viz
    presentation_path = None
    theme_override = None

    if presentation is not None:
        from pathlib import Path
        from .rendering import Presentation

        if isinstance(presentation, (str, Path)):
            # Path to presentation file
            presentation_path = presentation
        elif isinstance(presentation, Presentation):
            # Extract theme from Presentation object
            theme_override = presentation.theme
            # TODO: In the future, we could serialize and pass the full object
        elif isinstance(presentation, dict):
            # Extract theme from dict if present
            theme_override = presentation.get("theme")
            # TODO: Could create a temporary file or enhance generate_viz

    return generate_viz(
        document_path=ast,
        adapter_spec=adapter,
        output_format=output,
        presentation=presentation_path,
        theme=theme_override,
    )
