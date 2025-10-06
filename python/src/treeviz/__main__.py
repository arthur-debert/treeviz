"""
Entry point for treeviz CLI.

This module contains the CLI interface for treeviz.
"""

import os
import sys
from pathlib import Path

import click
from clier.cmdhelp import HelpConfig, HelpSystem, create_help_command

from treeviz.viz import generate_viz


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
      3viz viz document.json                  # Visualize with auto-detection
      3viz viz document.md mdast              # Use Markdown AST adapter
      echo '{"type":"root"}' | 3viz viz - 3viz   # Process from stdin

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
def viz(
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
    Visualize a document tree using a 3viz adapter.

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
      3viz viz document.json                  # Auto-detect format, use 3viz adapter
      3viz viz document.md mdast              # Use Markdown AST adapter
      3viz viz data.xml my-custom.yaml        # Use custom adapter definition
      3viz viz - mdast < input.json           # Read from stdin

    \b
    User-defined adapters are discovered from:
      ./.3viz/, ~/.config/3viz/, ~/.3viz/
    """

    print(
        generate_viz(
            document_path=document,
            adapter_spec=adapter,
            document_format=document_format,
            adapter_format=adapter_format,
            output_format=output_format or ctx.obj["output_format"],
            terminal_width=ctx.obj.get("terminal_width", None),
            theme=theme,
            presentation=presentation,
        ),
        end="",
    )


@cli.command()
def foo():
    """Test command that prints bar."""
    print("bar")


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
    cli()


if __name__ == "__main__":
    main()
