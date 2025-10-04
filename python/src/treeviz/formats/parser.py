"""
Document format parser.

This module provides the main parse_document function and format registry
for handling multiple document formats.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from .model import Format, DocumentFormatError
from .pformat import parse_pformat
from .xml_format import parse_xml

# Global format registry
_FORMATS: Dict[str, Format] = {}


def register_format(format_obj: Format) -> None:
    """
    Register a new document format.

    Args:
        format_obj: Format instance to register
    """
    _FORMATS[format_obj.name.lower()] = format_obj


def get_supported_formats() -> List[str]:
    """
    Get list of supported format names.

    Returns:
        List of format names
    """
    return list(_FORMATS.keys())


def get_format_by_name(name: str) -> Optional[Format]:
    """
    Get format by name.

    Args:
        name: Format name (case-insensitive)

    Returns:
        Format instance or None if not found
    """
    return _FORMATS.get(name.lower())


def detect_format(file_path: str) -> Optional[Format]:
    """
    Auto-detect format based on file extension.

    Args:
        file_path: Path to the file

    Returns:
        Format instance or None if no format can handle the file
    """
    for format_obj in _FORMATS.values():
        if format_obj.can_handle(file_path):
            return format_obj
    return None


def parse_document(file_path: str, format_name: Optional[str] = None) -> Any:
    """
    Parse a document file into a Python object.

    This function is orthogonal to the adapter system - it simply converts
    various input formats into Python objects that adapters can then process.

    Args:
        file_path: Path to the document file
        format_name: Optional format name. If None, auto-detects from extension

    Returns:
        Parsed Python object (usually dict or list)

    Raises:
        DocumentFormatError: If parsing fails or format is unsupported
        FileNotFoundError: If file doesn't exist
    """
    # Check if file exists
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine format
    if format_name:
        format_obj = get_format_by_name(format_name)
        if not format_obj:
            raise DocumentFormatError(
                f"Unsupported format: {format_name}. "
                f"Supported formats: {', '.join(get_supported_formats())}"
            )
    else:
        format_obj = detect_format(file_path)
        if not format_obj:
            raise DocumentFormatError(
                f"Cannot detect format for file: {file_path}. "
                f"Supported extensions: {_get_all_extensions()}"
            )

    # Read and parse file
    try:
        content = path.read_text(encoding="utf-8")
        return format_obj.parse(content)
    except UnicodeDecodeError as e:
        raise DocumentFormatError(
            f"Failed to read file as UTF-8: {file_path}"
        ) from e


def load_document(document_input, format_name: Optional[str] = None) -> Any:
    """
    Load a document from file, stdin, or Python object.

    This function handles multiple input types:
    - File paths: Load and parse from file system
    - Stdin: Use '-' as document_input to read from stdin
    - Python objects: Return directly (dict, list, etc.)

    Args:
        document_input: Path to document file, '-' for stdin, or Python object (dict/list)
        format_name: Optional format name. If None, auto-detects from extension
                    (stdin defaults to JSON if format_name not specified)

    Returns:
        Parsed Python object (usually dict or list)

    Raises:
        DocumentFormatError: If parsing fails or format is unsupported
        FileNotFoundError: If file doesn't exist (not applicable for stdin)
        TypeError: If document_input is not a supported type
    """
    # Handle Python objects directly
    if not isinstance(document_input, str):
        # Already a Python object (dict, list, etc.) - return as-is
        return document_input

    # Handle string inputs (file paths or stdin)
    file_path = document_input
    # Handle stdin input
    if file_path == "-":
        content = sys.stdin.read()

        if format_name:
            # Use specified format for stdin
            format_obj = get_format_by_name(format_name)
            if not format_obj:
                raise DocumentFormatError(
                    f"Unsupported format: {format_name}. "
                    f"Supported formats: {', '.join(get_supported_formats())}"
                )
        else:
            # Default to JSON for stdin
            format_obj = get_format_by_name("json")
            if not format_obj:
                raise DocumentFormatError(
                    "JSON format not available for stdin parsing"
                )

        try:
            return format_obj.parse(content)
        except Exception as e:
            if not format_name:
                # If we defaulted to JSON and it failed, give helpful error
                raise DocumentFormatError(
                    f"Failed to parse stdin as JSON. Use --document-format to specify format. "
                    f"Supported formats: {', '.join(get_supported_formats())}"
                ) from e
            else:
                raise DocumentFormatError(
                    f"Failed to parse stdin as {format_name}: {str(e)}"
                ) from e

    # Use existing parse_document for regular files
    return parse_document(file_path, format_name)


def _get_all_extensions() -> List[str]:
    """Get all supported file extensions."""
    extensions = []
    for format_obj in _FORMATS.values():
        extensions.extend(format_obj.extensions)
    return sorted(set(extensions))


# Built-in JSON format
def _parse_json(content: str) -> Any:
    """Parse JSON content."""
    return json.loads(content)


# Register built-in formats
register_format(
    Format(
        name="JSON",
        extensions=[".json", ".jsonl"],
        parse_func=_parse_json,
        description="JavaScript Object Notation",
    )
)


# Optional YAML format (requires ruamel.yaml)
try:
    from ruamel import yaml

    def _parse_yaml(content: str) -> Any:
        """Parse YAML content."""
        yml = yaml.YAML(typ="safe")
        return yml.load(content)

    register_format(
        Format(
            name="YAML",
            extensions=[".yaml", ".yml"],
            parse_func=_parse_yaml,
            description="YAML Ain't Markup Language",
        )
    )

except ImportError:
    # YAML support is optional
    pass


# Pformat (Pseudo Document Format) support

register_format(
    Format(
        name="Pformat",
        extensions=[".pformat", ".pf"],
        parse_func=parse_pformat,
        description="Pseudo Document Format (XML-like)",
    )
)


# XML format support (using xml.etree.ElementTree)

register_format(
    Format(
        name="XML",
        extensions=[".xml"],
        parse_func=parse_xml,
        description="Extensible Markup Language",
    )
)


# HTML format support (requires BeautifulSoup4)
try:
    from .html_format import parse_html

    register_format(
        Format(
            name="HTML",
            extensions=[".html", ".htm"],
            parse_func=parse_html,
            description="HyperText Markup Language",
        )
    )

except ImportError:
    # HTML support is optional (requires BeautifulSoup4)
    pass
