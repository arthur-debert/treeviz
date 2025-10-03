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


# Create the get-definition command dynamically
def _make_get_definition_command():
    """Create get-definition command with proper dynamic docstring."""
    # Get available formats dynamically
    available_formats = ["3viz"] + Lib.list_formats()
    format_list = ", ".join(available_formats)

    def get_definition_impl(ctx, format_name):
        """Call the main business logic for get-definition."""
        from . import __main__
        
        output_format = ctx.obj["format"]
        __main__.get_definition(format_name, output_format)

    # Set the docstring before applying decorators
    get_definition_impl.__doc__ = f"""
    Get a definition for the specified format.

    FORMAT_NAME: Name of the format ({format_list})
    """

    # Apply decorators
    return cli.command("get-definition")(
        click.argument(
            "format_name",
            type=click.Choice(Lib.list_formats() + ["3viz"]),
            default="3viz",
        )(click.pass_context(get_definition_impl))
    )


# Create the command
get_definition = _make_get_definition_command()


if __name__ == "__main__":
    cli()