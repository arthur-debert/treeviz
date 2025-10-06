"""
Learn command system for displaying documentation topics.

This module provides a reusable learn/topic system that can be integrated into any
Click-based CLI application. It supports:
- Dynamic discovery of topics from files
- Configurable topic directories
- Optional pager support for long content
- Configurable command name when mounting
"""

import os
import subprocess
import sys
from typing import List, Optional
from pathlib import Path

import click


class LearnSystem:
    """Main learn system implementation."""

    def __init__(
        self,
        topic_dirs: List[Path],
        file_extension: str = ".md",
        pager: Optional[str] = None,
    ):
        """
        Initialize the learn system.

        Args:
            topic_dirs: List of directories to search for topic files
            file_extension: File extension for topic files (default: ".md")
            pager: Default pager command (None means use system default)
        """
        self.topic_dirs = topic_dirs
        self.file_extension = file_extension
        self.pager = pager

    def discover_topics(self) -> List[str]:
        """Discover available topics from configured directories."""
        topics = set()

        for topic_dir in self.topic_dirs:
            if topic_dir.exists() and topic_dir.is_dir():
                pattern = f"*{self.file_extension}"
                for file_path in topic_dir.glob(pattern):
                    topics.add(file_path.stem)

        return sorted(topics)

    def load_topic(self, topic_name: str) -> Optional[str]:
        """
        Load content for a specific topic.

        Args:
            topic_name: Name of the topic

        Returns:
            The topic content as a string, or None if not found
        """
        for topic_dir in self.topic_dirs:
            topic_file = topic_dir / f"{topic_name}{self.file_extension}"
            if topic_file.exists():
                try:
                    return topic_file.read_text()
                except Exception as e:
                    click.echo(
                        f"Error reading topic '{topic_name}': {e}", err=True
                    )
                    return None

        return None

    def display_topic(self, content: str, use_pager: bool = False):
        """
        Display topic content, optionally using a pager.

        Args:
            content: The content to display
            use_pager: Whether to use a pager for display
        """
        if use_pager:
            # Try to use configured pager, then PAGER env var, then defaults
            pager = self.pager or os.environ.get("PAGER")

            if not pager:
                # Try common pagers
                for candidate in ["less", "more"]:
                    try:
                        subprocess.run(
                            ["which", candidate],
                            capture_output=True,
                            check=True,
                        )
                        pager = candidate
                        break
                    except subprocess.CalledProcessError:
                        continue

            if pager:
                try:
                    proc = subprocess.Popen(
                        pager, shell=True, stdin=subprocess.PIPE
                    )
                    proc.communicate(content.encode())
                except Exception:
                    # Fallback to direct output if pager fails
                    click.echo(content)
            else:
                click.echo(content)
        else:
            click.echo(content)

    def format_topic_list(self, command_name: str) -> str:
        """
        Format the list of available topics.

        Args:
            command_name: The name of the command (e.g., 'learn', 'topic')

        Returns:
            Formatted list of topics
        """
        topics = self.discover_topics()

        if not topics:
            return "No topics found."

        lines = ["Available topics:", ""]

        for topic in topics:
            lines.append(f"  {topic}")

        lines.append("")
        lines.append(f"To view a topic: {command_name} <topic>")
        lines.append(f"To view with pager: {command_name} <topic> --pager")

        return "\n".join(lines)


def create_learn_command(
    learn_system: LearnSystem,
    command_name: str = "learn",
    command_help: Optional[str] = None,
) -> click.Command:
    """
    Create a learn command with configurable name.

    Args:
        learn_system: The learn system instance
        command_name: Name for the command (default: "learn")
        command_help: Custom help text for the command

    Returns:
        A Click command configured as a learn command
    """
    if not command_help:
        command_help = "Display documentation topics."

    @click.command(name=command_name, help=command_help)
    @click.argument("topic", required=False)
    @click.option(
        "--pager", "-p", is_flag=True, help="Display topic using system pager"
    )
    def learn_cmd(topic, pager):
        """Display documentation topics."""
        if not topic:
            # List available topics
            output = learn_system.format_topic_list(command_name)
            click.echo(output)
        else:
            # Display specific topic
            content = learn_system.load_topic(topic)
            if content is None:
                click.echo(f"Topic '{topic}' not found.", err=True)
                click.echo("")
                click.echo(learn_system.format_topic_list(command_name))
                sys.exit(1)
            else:
                learn_system.display_topic(content, use_pager=pager)

    return learn_cmd
