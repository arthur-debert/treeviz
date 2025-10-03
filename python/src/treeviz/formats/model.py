"""
Format model for document parsing.

This module defines the Format dataclass that encapsulates document
format parsing functionality and file extension handling.
"""

from dataclasses import dataclass, field
from typing import List, Callable, Any
from pathlib import Path


class DocumentFormatError(Exception):
    """Exception raised when document parsing fails."""

    pass


@dataclass
class Format:
    """
    Document format definition.

    Encapsulates the parsing function and file extensions for a specific
    document format. This allows the system to auto-detect formats and
    parse documents appropriately.
    """

    name: str = field(
        metadata={
            "doc": "Human-readable name of the format (e.g., 'JSON', 'YAML')"
        }
    )

    extensions: List[str] = field(
        metadata={
            "doc": "File extensions this format handles (e.g., ['.json', '.jsonl'])"
        }
    )

    parse_func: Callable[[str], Any] = field(
        metadata={
            "doc": "Function that parses file content and returns Python object"
        }
    )

    description: str = field(
        default="", metadata={"doc": "Optional description of the format"}
    )

    def can_handle(self, file_path: str) -> bool:
        """
        Check if this format can handle the given file path.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this format can handle the file
        """
        path = Path(file_path)
        return path.suffix.lower() in [ext.lower() for ext in self.extensions]

    def parse(self, content: str) -> Any:
        """
        Parse the given content using this format's parser.

        Args:
            content: File content to parse

        Returns:
            Parsed Python object

        Raises:
            DocumentFormatError: If parsing fails
        """
        try:
            return self.parse_func(content)
        except Exception as e:
            raise DocumentFormatError(
                f"Failed to parse content as {self.name}: {e}"
            ) from e
