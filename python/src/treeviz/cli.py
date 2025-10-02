"""
3viz CLI

This module provides a standalone CLI for the 3viz tool.
"""

import json
from pathlib import Path

import click

from treeviz.renderer import Renderer
from treeviz.config import get_default_config, get_builtin_config, _load_config_file


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
    help="Output file path (default: prints to stdout)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format (default: json)"
)
def config_sample(output, format):
    """
    Generate a sample configuration file.
    """
    config_data = _load_config_file('sample.json')
    
    if format == "json":
        content = json.dumps(config_data, indent=2)
    else:  # yaml
        try:
            import yaml
            content = yaml.dump(config_data, default_flow_style=False, indent=2)
        except ImportError:
            click.echo("YAML support requires 'pyyaml' package. Install with: pip install pyyaml", err=True)
            return
    
    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Sample configuration written to {output}")
    else:
        click.echo(content)


@config.command("builtin")
@click.argument("format_name", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(), 
    help="Output file path (default: prints to stdout)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format (default: json)"
)
def config_builtin(format_name, output, format):
    """
    Export a built-in configuration.
    
    FORMAT_NAME: Name of the built-in format (mdast, json, etc.)
    """
    try:
        config_data = get_builtin_config(format_name)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return
    
    if format == "json":
        content = json.dumps(config_data, indent=2)
    else:  # yaml
        try:
            import yaml
            content = yaml.dump(config_data, default_flow_style=False, indent=2)
        except ImportError:
            click.echo("YAML support requires 'pyyaml' package. Install with: pip install pyyaml", err=True)
            return
    
    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Built-in configuration '{format_name}' written to {output}")
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()
