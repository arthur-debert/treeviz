"""
3viz CLI

This module provides argument parsing for the 3viz tool.
Business logic is implemented in __main__.py.
"""

import sys

import click

from .definitions import Lib


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
    A standalone CLI for the 3viz AST visualization tool.

    Examples:
      3viz doc.json                           # Use 3viz adapter, auto-detect format
      3viz doc.md mdast                       # Use built-in mdast adapter
      3viz doc.xml my-adapter.yaml            # Use custom adapter file
      3viz - mdast < input.json               # Read from stdin with mdast adapter
      cat data.json | 3viz -                  # Read from stdin with default adapter
      3viz get-definition mdast               # Get mdast adapter definition
    """
    # Ensure context dict exists
    ctx.ensure_object(dict)

    # Auto-detect format if not specified
    if output_format is None:
        output_format = "term" if sys.stdout.isatty() else "text"

    ctx.obj["output_format"] = output_format


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
@click.pass_context
def render(
    ctx, document, adapter, document_format, adapter_format, output_format
):
    """
    Render a document using 3viz.

    DOCUMENT: Path to document file or '-' for stdin
    ADAPTER: Adapter name (3viz, mdast, unist) or path to adapter file (default: 3viz)
    """
    # Use command-specific output format if provided, otherwise use global setting
    if output_format is None:
        output_format = ctx.obj["output_format"]

    # Run the render logic
    from . import __main__

    try:
        result = __main__.generate_viz(
            document_path=document,
            adapter_spec=adapter,
            document_format=document_format,
            adapter_format=adapter_format,
            output_format=output_format,
        )

        # Output result to stdout
        print(result, end="")

    except Exception as e:
        if output_format == "json":
            import json

            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@cli.command("get-definition")
@click.argument(
    "format_name",
    type=click.Choice(["3viz"] + Lib.list_formats()),
    default="3viz",
)
@click.pass_context
def get_definition(ctx, format_name):
    """
    Get a definition for the specified format.

    FORMAT_NAME: Name of the format (3viz, mdast, unist)
    """
    from . import __main__

    output_format = ctx.obj["output_format"]
    __main__.get_definition(format_name, output_format)


if __name__ == "__main__":
    cli()
