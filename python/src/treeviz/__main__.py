"""
Entry point for treeviz CLI.

This module contains the main business logic for the treeviz command-line interface.
The CLI module handles argument parsing and calls functions from this module.
"""

import json
import sys
from dataclasses import asdict

from .definitions import Lib, Definition


def get_definition(format_name, output_format):
    """
    Get a definition for the specified format.

    Args:
        format_name: Name of the format ('3viz' or format from Lib.list_formats())
        output_format: Output format ('text', 'json', 'term')

    Returns:
        None (outputs to stdout)
    """
    try:
        if format_name == "3viz":
            # Use the default 3viz definition
            def_data = asdict(Definition.default())
        else:
            # Get format from library
            def_data = asdict(Lib.get(format_name))
    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    _output_data(def_data, output_format)


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


def main():
    """Main entry point that delegates to CLI argument parsing."""
    from .cli import cli

    cli()


if __name__ == "__main__":
    main()
