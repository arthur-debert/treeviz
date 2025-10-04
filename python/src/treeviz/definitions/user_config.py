"""
User configuration directory discovery for treeviz.

This module handles finding and validating user-defined adapter libraries
in standard configuration directories.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional


def get_user_config_dirs(
    env_vars: Optional[Dict[str, str]] = None
) -> List[Path]:
    """
    Get list of user configuration directories to check for 3viz definitions.

    Checks for .3viz directories in:
    1. Current working directory (./.3viz)
    2. XDG_CONFIG_HOME/3viz or ~/.config/3viz
    3. Home directory (~/.3viz)

    Args:
        env_vars: Environment variables dict for testing (default: os.environ)

    Returns:
        List of Path objects for directories that should be checked
    """
    if env_vars is None:
        env_vars = os.environ

    config_dirs = []

    # 1. Current working directory
    cwd_config = Path.cwd() / ".3viz"
    config_dirs.append(cwd_config)

    # 2. XDG config directory with fallback
    xdg_config_home = env_vars.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        xdg_config_dir = Path(xdg_config_home) / "3viz"
    else:
        # Fallback to ~/.config/3viz
        home = Path.home()
        xdg_config_dir = home / ".config" / "3viz"
    config_dirs.append(xdg_config_dir)

    # 3. Home directory
    home_config = Path.home() / ".3viz"
    config_dirs.append(home_config)

    return config_dirs


def is_3viz_conf_dir(directory_path: Path) -> bool:
    """
    Check if a directory is a valid 3viz configuration directory.

    A directory is considered valid if:
    - It exists
    - It contains at least one .json, .yaml, or .yml file
    - If it contains config.json or config.yaml, it's still valid for future use

    Args:
        directory_path: Path to check

    Returns:
        True if directory is a valid 3viz config directory
    """
    if not directory_path.exists() or not directory_path.is_dir():
        return False

    # Check for definition files
    patterns = ["*.json", "*.yaml", "*.yml"]
    for pattern in patterns:
        if list(directory_path.glob(pattern)):
            return True

    return False


def discover_user_definitions(
    env_vars: Optional[Dict[str, str]] = None
) -> Dict[Path, List[Path]]:
    """
    Discover all user definition files in configuration directories.

    Args:
        env_vars: Environment variables dict for testing (default: os.environ)

    Returns:
        Dict mapping config directory paths to lists of definition files found
    """
    discovered = {}
    config_dirs = get_user_config_dirs(env_vars)

    for config_dir in config_dirs:
        if is_3viz_conf_dir(config_dir):
            definition_files = []
            patterns = ["*.json", "*.yaml", "*.yml"]
            for pattern in patterns:
                for file_path in config_dir.glob(pattern):
                    # Skip config files - these are for future configuration use
                    if file_path.stem.lower() in ["config", "3viz"]:
                        continue
                    definition_files.append(file_path)

            if definition_files:
                discovered[config_dir] = definition_files

    return discovered
