"""
Generic command-line help system for displaying markdown-based help topics.

This module provides a reusable help system that can be integrated into any
Click-based CLI application. It supports:
- Dynamic discovery of help topics from markdown files
- Configurable help directories
- Built-in and custom topic descriptions
- Integration with Click command groups
"""

from typing import List
from pathlib import Path
from dataclasses import dataclass

import click


@dataclass
class HelpConfig:
    """Configuration for the help system."""

    # List of directories to search for help topics (in priority order)
    help_dirs: List[Path]

    # File extension for help files
    file_extension: str = ".md"


class HelpSystem:
    """Main help system implementation."""

    def __init__(self, config: HelpConfig):
        """
        Initialize the help system with configuration.

        Args:
            config: Configuration for the help system
        """
        self.config = config

    def discover_topics(self) -> List[str]:
        """Discover available help topics from configured directories."""
        topics = set()

        for help_dir in self.config.help_dirs:
            if help_dir.exists() and help_dir.is_dir():
                pattern = f"*{self.config.file_extension}"
                for file_path in help_dir.glob(pattern):
                    topics.add(file_path.stem)

        return sorted(topics)

    def load_topic(self, topic_name: str) -> str:
        """
        Load help content for a specific topic.

        Args:
            topic_name: Name of the help topic

        Returns:
            The help content as a string
        """
        for help_dir in self.config.help_dirs:
            help_file = help_dir / f"{topic_name}{self.config.file_extension}"
            if help_file.exists():
                try:
                    return help_file.read_text()
                except Exception as e:
                    return f"Error reading help topic '{topic_name}': {e}"

        return f"Help topic '{topic_name}' not found."

    def format_topic_list(self) -> str:
        """Format the list of available topics."""
        topics = self.discover_topics()

        if not topics:
            return "No help topics found."

        lines = ["Available help topics:", ""]

        for topic in topics:
            lines.append(f"  {{app_name}} help {topic}")

        lines.append("")
        lines.append("For detailed information: {app_name} help <topic>")

        return "\n".join(lines)


class HelpGroup(click.Group):
    """
    Custom Click group that integrates with the help system.

    This group dynamically creates commands for each help topic discovered
    by the help system.
    """

    def __init__(self, help_system: HelpSystem, app_name: str, *args, **kwargs):
        """
        Initialize the help group.

        Args:
            help_system: The help system instance
            app_name: Name of the application (for display in help)
            *args, **kwargs: Additional arguments for Click Group
        """
        super().__init__(*args, **kwargs)
        self.help_system = help_system
        self.app_name = app_name
        self._dynamic_commands = {}
        self._load_dynamic_commands()

    def _load_dynamic_commands(self):
        """Load help topics as dynamic commands."""
        topics = self.help_system.discover_topics()

        for topic in topics:
            # Create a command for each topic
            def make_help_command(topic_name):
                def help_command():
                    content = self.help_system.load_topic(topic_name)
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
        """Get a command, checking dynamic commands first."""
        if cmd_name in self._dynamic_commands:
            return self._dynamic_commands[cmd_name]
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        """List only static commands (not dynamic help topics)."""
        return super().list_commands(ctx)

    def format_help(self, ctx, formatter):
        """Format help to include available topics."""
        super().format_help(ctx, formatter)

        topics = self.help_system.discover_topics()
        if topics:
            with formatter.section("Available Topics"):
                formatter.write_paragraph()
                for topic in topics:
                    formatter.write_text(f"  {self.app_name} help {topic}")


def create_help_command(help_system: HelpSystem, app_name: str) -> click.Group:
    """
    Create a help command group with list command.

    Args:
        help_system: The help system instance
        app_name: Name of the application

    Returns:
        A Click group configured as a help command
    """

    @click.group(cls=HelpGroup, help_system=help_system, app_name=app_name)
    def help_cmd():
        """
        Show detailed help for specific topics.

        Provides comprehensive documentation loaded from markdown files.
        """
        pass

    @help_cmd.command(name="list")
    def list_topics():
        """List all available help topics."""
        # Format the topic list with the app name
        output = help_system.format_topic_list()
        output = output.replace("{app_name}", app_name)
        click.echo(output)

    return help_cmd
