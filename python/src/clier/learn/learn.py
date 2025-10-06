"""
Learn command system for displaying documentation topics.

This module provides a reusable topcis app that
Click-based CLI application. It supports:
- Dynamic discovery of topics from files
- Configurable topic directories
- Optional pager support for long content

TODO: separate the main logic from the click bits.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click


def learn_app(
    topic_dirs: List[Path],
    file_extensions: tuple[str, ...] = (".md", ".txt"),
    pager: Optional[str] = None,
) -> click.Command:
    """
    Create a learn command for displaying documentation topics.

    Args:
        topic_dirs: List of directories to search for topic files
        file_extensions: Tuple of file extensions to search for (default: (".md", ".txt"))
        pager: Default pager command (None means use system default)

    Returns:
        A Click command ready to be added to a CLI
    """

    def discover_topics() -> List[str]:
        """Discover available topics from configured directories."""
        topics = set()

        for topic_dir in topic_dirs:
            if topic_dir.exists() and topic_dir.is_dir():
                for ext in file_extensions:
                    pattern = f"*{ext}"
                    for file_path in topic_dir.glob(pattern):
                        topics.add(file_path.stem)

        return sorted(topics)

    def load_topic(topic_name: str) -> Optional[str]:
        """Load content for a specific topic."""
        for topic_dir in topic_dirs:
            for ext in file_extensions:
                topic_file = topic_dir / f"{topic_name}{ext}"
                if topic_file.exists():
                    try:
                        return topic_file.read_text()
                    except Exception as e:
                        click.echo(
                            f"Error reading topic '{topic_name}': {e}", err=True
                        )
                        return None

        return None

    def display_topic(content: str, use_pager: bool = False):
        """Display topic content, optionally using a pager."""
        if use_pager:
            # Try to use configured pager, then PAGER env var, then defaults
            pager_cmd = pager or os.environ.get("PAGER")

            if not pager_cmd:
                # Try common pagers
                for candidate in ["less", "more"]:
                    try:
                        subprocess.run(
                            ["which", candidate],
                            capture_output=True,
                            check=True,
                        )
                        pager_cmd = candidate
                        break
                    except subprocess.CalledProcessError:
                        continue

            if pager_cmd:
                try:
                    proc = subprocess.Popen(
                        pager_cmd, shell=True, stdin=subprocess.PIPE
                    )
                    proc.communicate(content.encode())
                except Exception:
                    # Fallback to direct output if pager fails
                    click.echo(content)
            else:
                click.echo(content)
        else:
            click.echo(content)

    def format_topic_list(command_name: str) -> str:
        """Format the list of available topics."""
        topics = discover_topics()

        if not topics:
            return "No topics found."

        lines = ["Available topics:", ""]

        for topic in topics:
            lines.append(f"  {topic}")

        lines.append("")
        lines.append(f"To view a topic: {command_name} <topic>")
        lines.append(f"To view with pager: {command_name} <topic> --pager")

        return "\n".join(lines)

    @click.command()
    @click.argument("topic", required=False)
    @click.option(
        "--pager",
        "-p",
        is_flag=True,
        help="Display topic using system pager",
    )
    @click.pass_context
    def learn_cmd(ctx, topic, pager):
        """Display documentation topics."""
        # Get the actual command name from context
        command_name = ctx.info_name

        if not topic:
            # List available topics
            output = format_topic_list(command_name)
            click.echo(output)
        else:
            # Display specific topic
            content = load_topic(topic)
            if content is None:
                click.echo(f"Topic '{topic}' not found.", err=True)
                click.echo("")
                click.echo(format_topic_list(command_name))
                sys.exit(1)
            else:
                display_topic(content, use_pager=pager)

    return learn_cmd
