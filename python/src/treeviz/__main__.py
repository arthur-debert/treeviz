"""
Entry point for treeviz CLI.

This module contains both the CLI interface and main business logic for treeviz.
"""

import json
import sys
import os
from dataclasses import asdict
from typing import Optional, Union, Dict, Any
from pathlib import Path

import click

from .definitions import AdapterLib, AdapterDef
from .definitions.yaml_utils import serialize_dataclass_to_yaml
from .definitions.user_lib_commands import (
    list_user_definitions,
    validate_user_definitions,
)
from .formats import load_document
from .adapters import load_adapter, convert_document
from .rendering import TemplateRenderer


def generate_viz(
    document_path: Union[str, Path, Dict, list, Any],
    adapter_spec: Union[str, Dict, Any] = "3viz",
    document_format: Optional[str] = None,
    adapter_format: Optional[str] = None,
    output_format: str = "term",
    terminal_width: Optional[int] = None,
    theme: Optional[str] = None,
    presentation: Optional[Union[str, Path]] = None,
) -> Union[str, Any]:
    """
    Generate 3viz visualization from document.

    Main orchestration function that coordinates document loading, adapter loading,
    conversion, and rendering. Supports both file paths and Python objects.

    Args:
        document_path: Path to document file, '-' for stdin, or Python object (dict/list/Node)
        adapter_spec: Adapter name, file path, or adapter dict/object (default: "3viz")
        document_format: Override document format detection (default: auto-detect)
        adapter_format: Override adapter format detection (default: auto-detect)
        output_format: Output format - json/yaml/text/term/obj (default: "term")
        terminal_width: Terminal width for text/term output (default: 80)
        theme: Theme override - 'dark' or 'light' (default: auto-detect)
        presentation: Path to presentation.yaml configuration file

    Returns:
        String output in the specified format, or Node object if output_format="obj"

    Raises:
        Various exceptions from sub-functions (DocumentFormatError, ValueError, etc.)
    """
    # Load the document
    document = load_document(document_path, format_name=document_format)

    # Load the adapter definition (icons are now in style)
    adapter_def, _ = load_adapter(adapter_spec, adapter_format=adapter_format)

    # Convert document to 3viz Node format
    node = convert_document(document, adapter_def)

    # Handle output format
    if output_format == "obj":
        # For obj output, return Node object directly
        return node
    elif output_format in ["json", "yaml"]:
        # For data formats, convert Node to dict and serialize
        if node is None:
            result_data = None
        else:
            result_data = asdict(node)

        if output_format == "json":
            return json.dumps(result_data, indent=2, ensure_ascii=False)
        else:  # yaml
            try:
                from .definitions.yaml_utils import serialize_dataclass_to_yaml

                if node is None:
                    return "null\n"
                return serialize_dataclass_to_yaml(node, include_comments=False)
            except ImportError:
                # Fallback to JSON if YAML not available
                return json.dumps(result_data, indent=2, ensure_ascii=False)

    elif output_format in ["text", "term"]:
        # For text/term formats, use the new template renderer
        if node is None:
            return ""  # Empty output for ignored nodes

        # Use provided terminal width or default
        if terminal_width is None:
            terminal_width = 80

        # Create options for the template renderer
        renderer = TemplateRenderer()

        # If presentation file is provided, use Presentation
        if presentation:
            from .rendering import PresentationLoader
            from pathlib import Path

            # Load presentation configuration
            loader = PresentationLoader()
            presentation_obj = loader.load_presentation_hierarchy(
                Path(presentation)
            )

            # Apply theme override if specified
            if theme:
                presentation_obj.theme_name = theme
                # Reload the theme
                from .config.loaders import create_config_loaders

                loaders = create_config_loaders()
                theme_obj = loaders.load_theme(theme)
                if theme_obj:
                    presentation_obj.theme = theme_obj

            # Override terminal width if specified
            if terminal_width:
                presentation_obj.view.max_width = terminal_width

            return renderer.render(node, presentation_obj)
        else:
            # Legacy dict-based options
            options = {
                "terminal_width": terminal_width,
                "format": output_format,
            }

            # Add theme if specified
            if theme:
                options["theme"] = theme

            return renderer.render(node, options)

    else:
        raise ValueError(f"Unknown output format: {output_format}")


def _output_definition(definition, output_format):
    """
    Output definition in the specified format.

    Args:
        definition: The AdapterDef object to output
        output_format: One of 'text', 'json', 'term'
    """
    if output_format == "json":
        data = asdict(definition)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format in ["text", "term"]:
        # For text/term output, use YAML with comments for better readability
        try:
            yaml_output = serialize_dataclass_to_yaml(
                definition, include_comments=True
            )
            print(yaml_output)
        except ImportError:
            # Fallback to JSON if YAML not available
            data = asdict(definition)
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def _output_data(data, output_format):
    """
    Output data in the specified format.

    Args:
        data: The data to output
        output_format: One of 'text', 'json', 'term'
    """
    if output_format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format in ["text", "term"]:
        # For text/term output, just pipe the JSON (simpler approach)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def get_definition(format_name: str, output_format: str = "text"):
    """
    Get and output an adapter definition for the specified format.

    Args:
        format_name: Name of the format (3viz, mdast, unist, etc.)
        output_format: Output format - json/text/term (default: "text")
    """
    if format_name == "3viz":
        # For 3viz, create a default definition
        definition = AdapterDef()
    else:
        # For other formats, get from the library
        definition = AdapterLib.get(format_name)

    _output_definition(definition, output_format)


# CLI functions moved from cli.py to avoid import issues


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
    3viz - Terminal AST visualizer for document trees

    Transform complex Abstract Syntax Trees into readable, line-based visualizations.
    Works with Markdown, XML, JSON, Pandoc, reStructuredText and custom formats.

    \b
    Quick Start:
      3viz document.json                      # Visualize with auto-detection
      3viz document.md mdast                  # Use Markdown AST adapter
      echo '{"type":"root"}' | 3viz - 3viz   # Process from stdin

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
def render(
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
    Render a document tree using a 3viz adapter.

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
      3viz document.json                      # Auto-detect format, use 3viz adapter
      3viz document.md mdast                  # Use Markdown AST adapter
      3viz data.xml my-custom.yaml            # Use custom adapter definition
      3viz - mdast < input.json               # Read from stdin
      3viz data.json --output-format json     # Output as JSON instead of visual
      3viz doc.xml my-adapter --document-format json  # Force document parsing as JSON

    \b
    User-defined adapters are discovered from:
      ./.3viz/, ~/.config/3viz/, ~/.3viz/
    """
    # Use command-specific output format if provided, otherwise use global setting
    if output_format is None:
        output_format = ctx.obj["output_format"]

    try:
        result = generate_viz(
            document_path=document,
            adapter_spec=adapter,
            document_format=document_format,
            adapter_format=adapter_format,
            output_format=output_format,
            terminal_width=ctx.obj.get("terminal_width", 80),
            theme=theme,
            presentation=presentation,
        )

        # Output result to stdout
        print(result, end="")

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@cli.command("get-definition")
@click.argument(
    "format_name",
    type=click.Choice(["3viz"] + AdapterLib.list_formats()),
    default="3viz",
)
@click.pass_context
def get_definition_cmd(ctx, format_name):
    """
    Get the adapter definition for a specific format.

    \b
    FORMAT_NAME: Built-in adapter name (3viz, mdast, unist, pandoc, restructuredtext)
                 or user-defined adapter name

    \b
    Shows the complete adapter definition including field mappings, icons,
    type overrides, and other configuration. Useful for understanding how
    an adapter works or as a starting point for creating custom adapters.

    \b
    Examples:
      3viz get-definition mdast              # Show Markdown AST adapter
      3viz get-definition 3viz               # Show default adapter
      3viz get-definition my-custom          # Show user-defined adapter
      3viz get-definition mdast --output-format json  # Output as JSON
    """
    output_format = ctx.obj["output_format"]
    get_definition(format_name, output_format)


@cli.command("themes")
@click.pass_context
def list_themes_cmd(ctx):
    """
    List available themes.

    \b
    Shows all available themes that can be used with the --theme option:
    - Built-in themes (default, minimal, high_contrast)
    - User-defined themes from configuration directories

    \b
    Examples:
      3viz themes                           # List all themes
      3viz themes --output-format json      # Machine-readable output
    """
    from .rendering.themes import list_available_themes

    output_format = ctx.obj["output_format"]
    themes = list_available_themes()

    if output_format == "json":
        print(json.dumps({"themes": themes}, indent=2))
    else:
        print("Available themes:")
        for theme in themes:
            print(f"  - {theme}")


@cli.command("list-user-defs")
@click.pass_context
def list_user_defs_cmd(ctx):
    """
    List user-defined adapter configurations and directories.

    \b
    Discovers and displays user-defined adapters from XDG-compliant locations:
      ./.3viz/                    # Project-specific adapters
      ~/.config/3viz/             # User configuration directory (XDG)
      ~/.3viz/                    # Legacy user directory

    \b
    Shows which directories exist, how many adapter definitions they contain,
    and lists all discovered user-defined adapters by name and location.
    User adapters can be referenced by name just like built-in adapters.

    \b
    Examples:
      3viz list-user-defs                    # Show user adapters in terminal format
      3viz list-user-defs --output-format json  # Machine-readable output

    \b
    User adapters take precedence order: .3viz/ > ~/.config/3viz/ > ~/.3viz/
    Built-in adapters always take precedence over user-defined ones.
    """
    output_format = ctx.obj["output_format"]

    # Get the data using pure Python function
    data = list_user_definitions()

    # Format output based on requested format
    if output_format == "json":
        print(json.dumps(data, indent=2))
    else:
        # Terminal-friendly format
        directories = data["directories"]
        definitions = data["definitions"]

        # Show directory status
        print("User configuration directories:")
        for dir_info in directories:
            status_indicator = {
                "found": "✓",
                "found_no_definitions": "○",
                "not_found": "✗",
            }.get(dir_info["status"], "?")

            print(f"  {status_indicator} {dir_info['path']}", end="")
            if dir_info["status"] == "found":
                print(f" ({dir_info['file_count']} definitions)")
            elif dir_info["status"] == "found_no_definitions":
                print(" (found, no definitions)")
            else:
                print(" (not found)")

        print()

        # Show available definitions
        if definitions:
            print("Available user definitions:")
            for def_info in definitions:
                print(
                    f"  • {def_info['name']} ({def_info['format']}) - {def_info['file_path']}"
                )
        else:
            print("No user definitions found.")


@cli.command("validate-user-defs")
@click.pass_context
def validate_user_defs_cmd(ctx):
    """
    Validate user-defined adapter definition files.

    \b
    Checks all discovered user adapter definition files for:
      • Valid JSON/YAML syntax
      • Required adapter definition fields
      • Proper structure and data types
      • Icon pack references (if using icon packs)

    \b
    Reports validation results with detailed error messages for debugging.
    Use this command to troubleshoot adapter definitions that aren't working.

    \b
    Examples:
      3viz validate-user-defs                # Validate all user adapters
      3viz validate-user-defs --output-format json  # Machine-readable results

    \b
    Common validation issues:
      • Missing required fields (label, type, children)
      • Invalid YAML/JSON syntax
      • Incorrect field types or values
      • Malformed icon pack references
    """
    output_format = ctx.obj["output_format"]

    # Get validation results using pure Python function
    data = validate_user_definitions()

    # Format output based on requested format
    if output_format == "json":
        print(json.dumps(data, indent=2))
    else:
        # Terminal-friendly format
        summary = data["summary"]
        valid_defs = data["valid_definitions"]
        invalid_defs = data["invalid_definitions"]

        print("Validation Summary:")
        print(f"  Total files: {summary['total_files']}")
        print(f"  Valid: {summary['valid_count']}")
        print(f"  Invalid: {summary['invalid_count']}")
        print(f"  Success rate: {summary['success_rate']:.1%}")
        print()

        if valid_defs:
            print("Valid definitions:")
            for def_info in valid_defs:
                print(
                    f"  ✓ {def_info['name']} ({def_info['format']}) - {def_info['file_path']}"
                )
            print()

        if invalid_defs:
            print("Invalid definitions:")
            for def_info in invalid_defs:
                print(
                    f"  ✗ {def_info['name']} ({def_info['format']}) - {def_info['file_path']}"
                )
                print(f"    Error: {def_info['error']}")
            print()

        if not valid_defs and not invalid_defs:
            print("No user definitions found to validate.")


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
    """
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
    pass


@help.command()
def list():
    """
    List all available help topics.

    \b
    Shows all discoverable help topics with brief descriptions.
    Help topics are automatically loaded from documentation files.
    """
    topics = _discover_help_topics()
    if topics:
        click.echo("Available help topics:")
        click.echo()
        for topic in topics:
            # Add brief descriptions for common topics
            descriptions = {
                "getting-started": "Basic usage, concepts, and quick start guide",
                "adapters": "Complete adapter system documentation",
                "examples": "Practical examples and common patterns",
                "3viz-output": "Understanding the visual output format",
            }
            desc = descriptions.get(topic, "Detailed help topic")
            click.echo(f"  3viz help {topic:<20} # {desc}")
        click.echo()
        click.echo("For detailed information: 3viz help <topic>")
    else:
        click.echo("No help topics found.")
        click.echo("Help content is loaded from docs/shell-help/ directory.")


def main():
    """Main entry point that delegates to CLI argument parsing."""
    # If no arguments or first argument doesn't look like a subcommand, inject 'render'
    if len(sys.argv) > 1 and sys.argv[1] not in [
        "render",
        "get-definition",
        "list-user-defs",
        "validate-user-defs",
        "themes",
        "help",
        "--help",
        "--version",
    ]:
        # Handle special case for stdin '-' or file paths
        if sys.argv[1] == "-" or not sys.argv[1].startswith("-"):
            # First argument looks like a document path, prepend 'render'
            sys.argv.insert(1, "render")

    cli()


if __name__ == "__main__":
    main()
