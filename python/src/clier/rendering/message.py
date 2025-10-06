"""
Message dataclass for simple command output.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MessageLevel(Enum):
    """Message severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"


@dataclass
class Message:
    """
    A simple message object for command output.

    Attributes:
        msg: The message content
        level: The message severity level
        details: Optional additional details
    """

    msg: str
    level: MessageLevel = MessageLevel.INFO
    details: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary for serialization."""
        result = {"message": self.msg, "level": self.level.value}
        if self.details:
            result["details"] = self.details
        return result
