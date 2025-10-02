"""
3viz CLI

This module provides a standalone CLI for the 3viz tool.
"""

import json
from pathlib import Path

import click

from treeviz.renderer import DEFAULT_SYMBOLS, Renderer
from treeviz.parsers import parse


@click.group()
def cli():
    """
    A standalone CLI for the 3viz AST visualization tool.
    """
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to a JSON file with custom symbols.",
)
def render(file, config):
    """
    Render a document as a 3viz tree.
    """
    # Read the input file
    input_text = Path(file).read_text()

    # Parse the document
    document = parse(input_text)


    symbols = DEFAULT_SYMBOLS
    if config:
        with open(config, "r") as f:
            custom_symbols = json.load(f)
            symbols.update(custom_symbols)

    # Render the Node tree
    renderer = Renderer(symbols=symbols)
    output = renderer.render(node_tree)

    # Print the output
    click.echo(output)


if __name__ == "__main__":
    cli()
