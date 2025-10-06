"""
Generic rendering layer for CLI applications.

Provides format-agnostic rendering with support for:
- JSON/YAML data serialization
- Text and terminal output with templates
- Message objects for simple command output
"""

from .message import Message, MessageLevel
from .renderer import render, handle_command_result

__all__ = ["Message", "MessageLevel", "render", "handle_command_result"]
