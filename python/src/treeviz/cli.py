"""
3viz CLI

This module provides argument parsing for the 3viz tool.
Business logic is implemented in __main__.py.
"""

import sys
from pathlib import Path

import click

from .definitions import Lib


def _get_help_dir() -> Path:
    """Get the help directory, handling both development and installed scenarios."""
    # Try development path first (relative to repo root)
    dev_help_dir = (
        Path(__file__).parent.parent.parent.parent / "docs" / "shell-help"
    )
    if dev_help_dir.exists():
        return dev_help_dir

    # For installed packages, use package data
    pkg_help_dir = Path(__file__).parent / "data" / "shell-help"
    if pkg_help_dir.exists():
        return pkg_help_dir

    # Last resort: return dev path even if it doesn't exist
    return dev_help_dir


def _load_help_topic(topic_name: str) -> str:
    """Load help content from markdown file."""
    help_dir = _get_help_dir()
    help_file = help_dir / f"{topic_name}.md"

    try:
        return help_file.read_text()
    except FileNotFoundError:
        return f"Help topic '{topic_name}' not found."


def _discover_help_topics() -> list:
    """Discover available help topics from markdown files."""
    help_dir = _get_help_dir()

    if not help_dir.exists():
        return []

    topics = []
    for md_file in help_dir.glob("*.md"):
        topics.append(md_file.stem)

    return sorted(topics)


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


class HelpGroup(click.Group):
    """Custom help group that dynamically discovers help topics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dynamic_commands = {}
        self._load_dynamic_commands()

    def _load_dynamic_commands(self):
        """Load help topics from markdown files."""
        topics = _discover_help_topics()
        for topic in topics:
            # Create a dynamic command for each topic
            def make_help_command(topic_name):
                def help_command():
                    content = _load_help_topic(topic_name)
                    click.echo(content)

                return help_command

            # Set up the command
            cmd = make_help_command(topic)
            cmd.__name__ = topic.replace("-", "_")
            cmd.__doc__ = f"Show help for {topic}"

            # Convert to Click command
            click_cmd = click.command(name=topic)(cmd)
            self._dynamic_commands[topic] = click_cmd

    def get_command(self, ctx, cmd_name):
        # First try dynamic commands
        if cmd_name in self._dynamic_commands:
            return self._dynamic_commands[cmd_name]

        # Fall back to regular commands
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        # Only list regular commands in the Commands section
        # Dynamic commands will be shown in Available Topics section
        return super().list_commands(ctx)

    def format_help(self, ctx, formatter):
        """Override help formatting to show available topics."""
        # Show the basic help first
        super().format_help(ctx, formatter)

        # Add available topics section
        topics = _discover_help_topics()
        if topics:
            with formatter.section("Available Topics"):
                formatter.write_paragraph()
                for topic in topics:
                    formatter.write_text(f"  3viz help {topic}")
                formatter.write_paragraph()
                formatter.write_text(
                    "Topics are loaded from markdown files in docs/shell-help/"
                )


@cli.group(cls=HelpGroup)
def help():
    """Shows help for specific topics.

    Help topics are loaded dynamically from markdown files in docs/shell-help/.
    """
    pass


@help.command()
def list():
    """List all available help topics."""
    topics = _discover_help_topics()
    if topics:
        click.echo("Available help topics:")
        for topic in topics:
            click.echo(f"  3viz help {topic}")
    else:
        click.echo("No help topics found.")

    click.echo("\nTo add new topics, create markdown files in docs/shell-help/")


if __name__ == "__main__":
    cli()
