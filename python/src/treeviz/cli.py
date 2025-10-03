"""
3viz CLI

This module provides a standalone CLI for the 3viz tool.
"""

import json

import click

from .definitions import (
    load_format_def,
)
from .definitions.schema import Definition


@click.group()
def cli():
    """
    A standalone CLI for the 3viz AST visualization tool.
    """
    pass


# Note: render command removed due to missing parsers module
# TODO: Re-enable when parsers module is available


@cli.group()
def def_():
    """
    Configuration management commands.
    """
    pass


@def_.command("sample")
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
def def_sample(output, format):
    """
    Generate a sample definition file.
    """
    # Generate a comprehensive sample definition
    sample_def = Definition(
        attributes={
            "label": "name",
            "type": "node_type",
            "children": "children",
        },
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
    def_data = sample_def.to_dict(merge_icons=False)

    if format == "json":
        content = json.dumps(def_data, indent=2)
    else:  # yaml
        try:
            import yaml

            content = yaml.dump(def_data, default_flow_style=False, indent=2)
        except ImportError:
            click.echo(
                "YAML support requires 'pyyaml' package. Install with: pip install pyyaml",
                err=True,
            )
            return

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Sample definition written to {output}")
    else:
        click.echo(content)


@def_.command("builtin")
@click.argument("format_name", type=str)
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
def def_builtin(format_name, output, format):
    """
    Export a built-in definition.

    FORMAT_NAME: Name of the built-in format (mdast, json, etc.)
    """
    try:
        def_data = load_format_def(format_name).to_dict()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return

    if format == "json":
        content = json.dumps(def_data, indent=2)
    else:  # yaml
        try:
            import yaml

            content = yaml.dump(def_data, default_flow_style=False, indent=2)
        except ImportError:
            click.echo(
                "YAML support requires 'pyyaml' package. Install with: pip install pyyaml",
                err=True,
            )
            return

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Built-in definition '{format_name}' written to {output}")
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()
