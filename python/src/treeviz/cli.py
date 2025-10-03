"""
3viz CLI

This module provides a standalone CLI for the 3viz tool.
"""

import json
import sys
from dataclasses import asdict

import click

from .definitions import Lib, Definition


@click.group()
@click.option(
    "--format",
    type=click.Choice(["text", "json", "term"]),
    default=None,
    help="Output format (default: term for terminals, text for pipes)",
)
@click.pass_context
def cli(ctx, format):
    """
    A standalone CLI for the 3viz AST visualization tool.
    """
    # Ensure context dict exists
    ctx.ensure_object(dict)

    # Auto-detect format if not specified
    if format is None:
        format = "term" if sys.stdout.isatty() else "text"

    ctx.obj["format"] = format


# Note: render command removed due to missing parsers module
# TODO: Re-enable when parsers module is available


@cli.command("get-definition")
@click.argument(
    "format_name",
    type=click.Choice(Lib.list_formats() + ["3viz"]),
    default="3viz",
)
@click.pass_context
def get_definition(ctx, format_name):
    """
    Get a definition for the specified format.

    FORMAT_NAME: Name of the format (dynamically sourced from Lib.list_formats() plus 3viz)
    """
    output_format = ctx.obj["format"]

    try:
        if format_name == "3viz":
            # Generate a comprehensive sample definition for 3viz
            sample_def = Definition(
                label="name",
                type="node_type",
                children="children",
                icons={
                    "document": "⧉",
                    "paragraph": "¶",
                    "heading": "⊤",
                    "list": "☰",
                    "custom_type": "★",
                },
                type_overrides={
                    "paragraph": {"label": "content"},
                    "heading": {"label": "title"},
                },
                ignore_types=["comment", "whitespace"],
            )
            def_data = asdict(sample_def)
        else:
            def_data = asdict(Lib.get(format_name))
    except Exception as e:
        if output_format == "json":
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(f"Error: {e}", err=True)
        return

    _output_data(def_data, output_format)


def _output_data(data, output_format):
    """
    Output data in the specified format.

    Args:
        data: The data to output
        output_format: One of 'text', 'json', 'term'
    """
    if output_format == "json":
        click.echo(json.dumps(data, indent=2))
    elif output_format in ["text", "term"]:
        # For text/term output, just pipe the JSON (simpler approach)
        click.echo(json.dumps(data, indent=2))
    else:
        raise ValueError(f"Unknown output format: {output_format}")


if __name__ == "__main__":
    cli()
