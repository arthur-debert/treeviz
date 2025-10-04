"""
Entry point for treeviz CLI.

This module contains the main business logic for the treeviz command-line interface.
The CLI module handles argument parsing and calls functions from this module.
"""

import json
import sys
import os
from dataclasses import asdict
from typing import Optional, Union, Dict, Any
from pathlib import Path

from .definitions import Lib, Definition
from .definitions.yaml_utils import serialize_dataclass_to_yaml
from .formats import load_document
from .adapters import load_adapter, convert_document
from .renderer import render, create_render_options


def get_definition(format_name, output_format):
    """
    Get a definition for the specified format.

    Args:
        format_name: Name of the format ('3viz' or format from Lib.list_formats())
        output_format: Output format ('text', 'json', 'term')

    Returns:
        None (outputs to stdout)
    """
    try:
        if format_name == "3viz":
            # Use the default 3viz definition
            definition = Definition.default()
        else:
            # Get format from library
            definition = Lib.get(format_name)
    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    _output_definition(definition, output_format)


def generate_viz(
    document_path: Union[str, Path, Dict, list, Any],
    adapter_spec: Union[str, Dict, Any] = "3viz",
    document_format: Optional[str] = None,
    adapter_format: Optional[str] = None,
    output_format: str = "term",
) -> Union[str, Any]:
    """
    Generate 3viz visualization from document.

    Main orchestration function that coordinates document loading, adapter loading,
    conversion, and rendering. Supports both file paths and Python objects.

    Args:
        document_path: Path to document file, '-' for stdin, or Python object (dict/list/Node)
        adapter_spec: Adapter name, file path, or adapter dict/object (default: "3viz")
        document_format: Override document format detection (default: auto-detect)
        adapter_format: Override adapter format detection (default: auto-detect)
        output_format: Output format - json/yaml/text/term/obj (default: "term")

    Returns:
        String output in the specified format, or Node object if output_format="obj"

    Raises:
        Various exceptions from sub-functions (DocumentFormatError, ValueError, etc.)
    """
    # Load the document
    document = load_document(document_path, format_name=document_format)

    # Load the adapter definition and icons
    adapter_def, icons_dict = load_adapter(
        adapter_spec, adapter_format=adapter_format
    )

    # Convert document to 3viz Node format
    node = convert_document(document, adapter_def)

    # Handle output format
    if output_format == "obj":
        # For obj output, return Node object directly
        return node
    elif output_format in ["json", "yaml"]:
        # For data formats, convert Node to dict and serialize
        if node is None:
            result_data = None
        else:
            result_data = asdict(node)

        if output_format == "json":
            return json.dumps(result_data, indent=2, ensure_ascii=False)
        else:  # yaml
            try:
                from .definitions.yaml_utils import serialize_dataclass_to_yaml

                if node is None:
                    return "null\n"
                return serialize_dataclass_to_yaml(node, include_comments=False)
            except ImportError:
                # Fallback to JSON if YAML not available
                return json.dumps(result_data, indent=2, ensure_ascii=False)

    elif output_format in ["text", "term"]:
        # For text/term formats, use the renderer
        if node is None:
            return ""  # Empty output for ignored nodes

        # Determine terminal width for formatting
        if output_format == "term":
            # Auto-detect terminal width
            terminal_width = (
                os.get_terminal_size().columns if sys.stdout.isatty() else 80
            )
        else:
            # Use standard width for text output (non-interactive)
            terminal_width = 80

        # Create render options with icons from adapter
        render_options = create_render_options(
            symbols=icons_dict, terminal_width=terminal_width
        )

        return render(node, render_options)

    else:
        raise ValueError(f"Unknown output format: {output_format}")


def _output_definition(definition, output_format):
    """
    Output definition in the specified format.

    Args:
        definition: The Definition object to output
        output_format: One of 'text', 'json', 'term'
    """
    if output_format == "json":
        data = asdict(definition)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format in ["text", "term"]:
        # For text/term output, use YAML with comments for better readability
        try:
            yaml_output = serialize_dataclass_to_yaml(
                definition, include_comments=True
            )
            print(yaml_output)
        except ImportError:
            # Fallback to JSON if YAML not available
            data = asdict(definition)
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def _output_data(data, output_format):
    """
    Output data in the specified format.

    Args:
        data: The data to output
        output_format: One of 'text', 'json', 'term'
    """
    if output_format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format in ["text", "term"]:
        # For text/term output, just pipe the JSON (simpler approach)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def main():
    """Main entry point that delegates to CLI argument parsing."""
    import sys
    from .cli import cli

    # If no arguments or first argument doesn't look like a subcommand, inject 'render'
    if len(sys.argv) > 1 and sys.argv[1] not in [
        "render",
        "get-definition",
        "help",
        "--help",
        "--version",
    ]:
        # Handle special case for stdin '-' or file paths
        if sys.argv[1] == "-" or not sys.argv[1].startswith("-"):
            # First argument looks like a document path, prepend 'render'
            sys.argv.insert(1, "render")

    cli()


if __name__ == "__main__":
    main()
