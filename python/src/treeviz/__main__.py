"""
Entry point for treeviz CLI.

This module contains the CLI interface for treeviz.
"""

import os
import sys
from pathlib import Path

import click
from clier.learn import learn_app

from treeviz.viz import generate_viz

# Configure learn system paths, has to work in editable and packaged..
ROOT = Path(Path(__file__).parent)
_topic_dirs = [ROOT / "docs" / "shell-help"]


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

    DOCUMENT: Path to document file or '-' for stdin
    ADAPTER:  Built-in adapter (3viz, mdast, unist, pandoc, restructuredtext),
              user-defined adapter name, or path to adapter definition file
    Examples:
      3viz viz document.json                  # Auto-detect format, use 3viz adapter
      3viz viz document.md mdast              # Use Markdown AST adapter
      3viz viz data.xml my-custom.yaml        # Use custom adapter definition
      3viz viz - mdast < input.json           # Read from stdin
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


# Create and add the learn command with custom name
cli.add_command(learn_app(_topic_dirs), name="learn")


def main():
    """Main entry point that delegates to CLI argument parsing."""
    cli()


if __name__ == "__main__":
    main()
