"""
3viz CLI

This module provides a standalone CLI for the 3viz tool.
"""

import json

import click

from treeviz.config import get_default_config


@click.group()
def cli():
    """
    A standalone CLI for the 3viz AST visualization tool.
    """
    pass


# Note: render command removed due to missing parsers module
# TODO: Re-enable when parsers module is available


@cli.group()
def config():
    """
    Configuration management commands.
    """
    pass


@config.command("sample")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: prints to stdout)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format (default: json)",
)
def sample(output, format):
    """
    Generate a sample configuration file.
    """

    # Get sample configuration
    config = get_default_config()

    if format == "json":
        output_text = json.dumps(config, indent=2)
    else:
        # YAML format (if requested, though not implemented)
        output_text = json.dumps(config, indent=2)  # Fallback to JSON

    if output:
        with open(output, "w") as f:
            f.write(output_text)
        click.echo(f"Sample configuration written to {output}")
    else:
        click.echo(output_text)


if __name__ == "__main__":
    cli()
