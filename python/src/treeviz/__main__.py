"""
Entry point for treeviz CLI.

This module contains both the CLI interface and main business logic for treeviz.
"""

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union

import click
from clier.cmdhelp import HelpConfig, HelpSystem, create_help_command

from .adapters import convert_document, load_adapter
from .definitions import AdapterDef, AdapterLib
from .definitions.yaml_utils import serialize_dataclass_to_yaml
from .formats import load_document
from .rendering import TemplateRenderer


def generate_viz(
    document_path: Union[str, Path, Dict, list, Any],
    adapter_spec: Union[str, Dict, Any] = "3viz",
    document_format: Optional[str] = None,
    adapter_format: Optional[str] = None,
    output_format: str = "term",
    terminal_width: Optional[int] = None,
    theme: Optional[str] = None,
    presentation: Optional[Union[str, Path]] = None,
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
        terminal_width: Terminal width for text/term output (default: 80)
        theme: Theme override - 'dark' or 'light' (default: auto-detect)
        presentation: Path to presentation.yaml configuration file

    Returns:
        String output in the specified format, or Node object if output_format="obj"

    Raises:
        Various exceptions from sub-functions (DocumentFormatError, ValueError, etc.)
    """
    # Load the document
    document = load_document(document_path, format_name=document_format)

    # Load the adapter definition (icons are now in style)
    adapter_def, _ = load_adapter(adapter_spec, adapter_format=adapter_format)

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
        # For text/term formats, use the new template renderer
        if node is None:
            return ""  # Empty output for ignored nodes

        # Use provided terminal width or default
        if terminal_width is None:
            terminal_width = 80

        # Create renderer and presentation
        renderer = TemplateRenderer()
        from pathlib import Path

        from .rendering import Presentation, PresentationLoader

        # Load presentation configuration
        if presentation:
            loader = PresentationLoader()
            presentation_obj = loader.load_presentation_hierarchy(
                Path(presentation)
            )
        else:
            # Create default presentation
            presentation_obj = Presentation()

        # Apply theme override if specified
        if theme:
            presentation_obj.theme_name = theme
            # Reload the theme
            from .config.loaders import create_config_loaders

            loaders = create_config_loaders()
            theme_obj = loaders.load_theme(theme)
            if theme_obj:
                presentation_obj.theme = theme_obj

        # Override terminal width if specified
        if terminal_width:
            presentation_obj.view.max_width = terminal_width

        return renderer.render(node, presentation_obj)

    else:
        raise ValueError(f"Unknown output format: {output_format}")


def _output_definition(definition, output_format):
    """
    Output definition in the specified format.

    Args:
        definition: The AdapterDef object to output
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


def get_definition(format_name: str, output_format: str = "text"):
    """
    Get and output an adapter definition for the specified format.

    Args:
        format_name: Name of the format (3viz, mdast, unist, etc.)
        output_format: Output format - json/text/term (default: "text")
    """
    if format_name == "3viz":
        # For 3viz, create a default definition
        definition = AdapterDef()
    else:
        # For other formats, get from the library
        definition = AdapterLib.get(format_name)

    _output_definition(definition, output_format)


# CLI functions moved from cli.py to avoid import issues

# Configure help system paths
_help_dirs = []

# Try development path first (relative to repo root)
_dev_help_dir = (
    Path(__file__).parent.parent.parent.parent / "docs" / "shell-help"
)
if _dev_help_dir.exists():
    _help_dirs.append(_dev_help_dir)

# For installed packages, use package data
_pkg_help_dir = Path(__file__).parent / "data" / "shell-help"
if _pkg_help_dir.exists():
    _help_dirs.append(_pkg_help_dir)

# If no directories found, still use dev path
if not _help_dirs:
    _help_dirs.append(_dev_help_dir)

# Create help system with just the directories
_help_config = HelpConfig(help_dirs=_help_dirs)
_help_system = HelpSystem(_help_config)


@click.group()
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml", "term"]),
    default=None,
    help="Output format (default: term for terminals, text for pipes)",
)
@click.pass_context
def cli(ctx, output_format):
    """
    3viz - Terminal AST visualizer for document trees

    Transform complex Abstract Syntax Trees into readable, line-based visualizations.
    Works with Markdown, XML, JSON, Pandoc, reStructuredText and custom formats.

    \b
    Quick Start:
      3viz document.json                      # Visualize with auto-detection
      3viz document.md mdast                  # Use Markdown AST adapter
      echo '{"type":"root"}' | 3viz - 3viz   # Process from stdin

    \b
    Available adapters: 3viz, mdast, unist, pandoc, restructuredtext
    For detailed help: 3viz help getting-started
    """
    # Ensure context dict exists
    ctx.ensure_object(dict)

    # Auto-detect format and terminal width if not specified
    is_tty = sys.stdout.isatty()
    if output_format is None:
        output_format = "term" if is_tty else "text"

    # Determine terminal width once
    terminal_width = os.get_terminal_size().columns if is_tty else 80

    ctx.obj["output_format"] = output_format
    ctx.obj["terminal_width"] = terminal_width
    ctx.obj["is_tty"] = is_tty


@cli.command()
@click.argument("document", type=click.Path(exists=False))
@click.argument("adapter", default="3viz")
@click.option(
    "--document-format",
    type=click.Choice(["json", "yaml", "xml", "html"]),
    help="Override document format detection",
)
@click.option(
    "--adapter-format",
    type=click.Choice(["json", "yaml"]),
    help="Override adapter format detection (only for file-based adapters)",
)
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml", "term"]),
    help="Output format (overrides global setting)",
)
@click.option(
    "--theme",
    help="Theme name (dark, light, minimal, high_contrast) or custom theme",
)
@click.option(
    "--presentation",
    type=click.Path(exists=True, readable=True),
    help="Path to presentation.yaml configuration file",
)
@click.pass_context
def render(
    ctx,
    document,
    adapter,
    document_format,
    adapter_format,
    output_format,
    theme,
    presentation,
):
    """
    Render a document tree using a 3viz adapter.

    \b
    DOCUMENT: Path to document file or '-' for stdin
    ADAPTER:  Built-in adapter (3viz, mdast, unist, pandoc, restructuredtext),
              user-defined adapter name, or path to adapter definition file

    \b
    The adapter defines how to extract and display information from your AST format.
    Built-in adapters handle common formats automatically. For custom formats,
    create an adapter definition file or use user-defined adapters.

    \b
    Examples:
      3viz document.json                      # Auto-detect format, use 3viz adapter
      3viz document.md mdast                  # Use Markdown AST adapter
      3viz data.xml my-custom.yaml            # Use custom adapter definition
      3viz - mdast < input.json               # Read from stdin
      3viz data.json --output-format json     # Output as JSON instead of visual
      3viz doc.xml my-adapter --document-format json  # Force document parsing as JSON

    \b
    User-defined adapters are discovered from:
      ./.3viz/, ~/.config/3viz/, ~/.3viz/
    """
    # Use command-specific output format if provided, otherwise use global setting
    if output_format is None:
        output_format = ctx.obj["output_format"]

    try:
        result = generate_viz(
            document_path=document,
            adapter_spec=adapter,
            document_format=document_format,
            adapter_format=adapter_format,
            output_format=output_format,
            terminal_width=ctx.obj.get("terminal_width", 80),
            theme=theme,
            presentation=presentation,
        )

        # Output result to stdout
        print(result, end="")

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# Create the help command using the generic help system
help = create_help_command(_help_system, "3viz")

# Update the docstring for the help command
help.__doc__ = """
Show detailed help for specific topics.

\b
Provides comprehensive documentation for 3viz features, including:
  • Getting started guides and basic usage
  • Adapter system and custom adapter creation
  • Advanced extraction and transform pipelines
  • Visual output format explanation
  • Examples and real-world use cases

\b
Examples:
  3viz help getting-started         # Basic usage and concepts
  3viz help adapters               # Adapter system documentation
  3viz help examples               # Practical examples and patterns

\b
All help content is loaded from markdown files for rich formatting.
"""

# Register the help command with the main CLI
cli.add_command(help)


def main():
    """Main entry point that delegates to CLI argument parsing."""
    # If no arguments or first argument doesn't look like a subcommand, inject 'render'
    if len(sys.argv) > 1 and sys.argv[1] not in [
        "render",
        "get-definition",
        "list-user-defs",
        "validate-user-defs",
        "themes",
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
