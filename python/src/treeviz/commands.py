"""
Command functions for treeviz CLI.

These functions implement the business logic and return result objects
that can be rendered in different formats.
"""

from pathlib import Path
from typing import Union, Optional, Dict, Any

from .viz import generate_viz
from .result import TreeResult
from clier.rendering import Message, MessageLevel


def viz_command(
    document_path: Union[str, Path, Dict, Any],
    adapter_spec: Union[str, Dict, Any] = "3viz",
    document_format: Optional[str] = None,
    adapter_format: Optional[str] = None,
    terminal_width: Optional[int] = None,
    theme: Optional[str] = None,
    presentation: Optional[Union[str, Path]] = None,
) -> TreeResult:
    """
    Execute the viz command and return a TreeResult.

    This is the clean command function that returns a result object
    instead of a rendered string.

    Args:
        document_path: Path to document or document object
        adapter_spec: Adapter specification
        document_format: Override document format detection
        adapter_format: Override adapter format detection
        terminal_width: Terminal width for rendering
        theme: Theme name
        presentation: Path to presentation config

    Returns:
        TreeResult object ready for rendering
    """
    return generate_viz(
        document_path=document_path,
        adapter_spec=adapter_spec,
        document_format=document_format,
        adapter_format=adapter_format,
        output_format="term",  # We'll handle format in rendering
        terminal_width=terminal_width,
        theme=theme,
        presentation=presentation,
        return_result_object=True,
    )


def version_command() -> Message:
    """Return version information."""
    # TODO: Get version from package metadata
    return Message("3viz version 1.0.0", level=MessageLevel.INFO)


def help_command() -> Message:
    """Return help information."""
    return Message(
        "Use '3viz learn' for interactive help and tutorials",
        level=MessageLevel.INFO,
        details="Run '3viz --help' for command line options",
    )
