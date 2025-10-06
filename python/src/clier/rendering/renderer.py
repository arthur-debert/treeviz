"""
Main rendering functions for the generic rendering layer.
"""

from pathlib import Path
from typing import Any, Dict, Optional, List

from .base import OutputFormat, Renderer
from .formatters import JSONFormatter, YAMLFormatter, TextFormatter
from .message import Message, MessageLevel


def get_renderer(
    format: OutputFormat, template_dirs: Optional[List[Path]] = None
) -> Renderer:
    """
    Get the appropriate renderer for the given format.

    Args:
        format: The output format
        template_dirs: Optional template directories for text rendering

    Returns:
        A renderer instance
    """
    if format == OutputFormat.JSON:
        return JSONFormatter()
    elif format == OutputFormat.YAML:
        return YAMLFormatter()
    elif format in (OutputFormat.TEXT, OutputFormat.TERM):
        return TextFormatter(template_dirs)
    else:
        raise ValueError(f"Unknown output format: {format}")


def render(
    data: Any,
    format: Optional[str] = None,
    template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    template_dirs: Optional[List[Path]] = None,
) -> str:
    """
    Render data in the specified format.

    Args:
        data: The data to render
        format: Output format (json, yaml, text, term, or None for auto-detect)
        template: Template name for text rendering
        context: Additional context for rendering
        template_dirs: Optional template directories

    Returns:
        Rendered string
    """
    # Detect format
    output_format = OutputFormat.detect(format)

    # Get renderer
    renderer = get_renderer(output_format, template_dirs)

    # Build context
    if context is None:
        context = {}
    context["format"] = output_format

    return renderer.render(data, template, context)


def handle_command_result(
    result: Any,
    output_format: Optional[str] = None,
    template_name: Optional[str] = None,
    template_dirs: Optional[List[Path]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Handle the result of a command execution.

    This is the main entry point for CLI commands to render their results.

    Args:
        result: The command result (object, Message, etc.)
        output_format: Desired output format (json, yaml, text, term, or None)
        template_name: Template to use for text rendering
        template_dirs: Additional template directories
        context: Additional rendering context

    Returns:
        Rendered string ready for output
    """
    # Special handling for None results
    if result is None:
        result = Message(
            "Command completed successfully", level=MessageLevel.SUCCESS
        )

    # Special handling for exceptions
    if isinstance(result, Exception):
        result = Message(
            f"Error: {str(result)}",
            level=MessageLevel.ERROR,
            details=f"{type(result).__name__}: {str(result)}",
        )

    return render(result, output_format, template_name, context, template_dirs)
