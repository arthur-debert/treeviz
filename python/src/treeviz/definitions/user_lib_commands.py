"""
Pure Python functions for user library management commands.

These functions implement the core logic for CLI commands, separate from 
output formatting to enable easy testing and reuse.
"""

from typing import Dict, Optional, Any, List
from pathlib import Path
import os

from .model import AdapterDef


def get_user_config_dirs(
    env_vars: Optional[Dict[str, str]] = None
) -> List[Path]:
    """
    Get user configuration directories in precedence order.

    Args:
        env_vars: Environment variables for testing (default: os.environ)

    Returns:
        List of paths in precedence order
    """
    if env_vars is None:
        env_vars = os.environ

    dirs = []

    # Project-specific directory (highest precedence)
    dirs.append(Path.cwd() / ".3viz")

    # XDG config home
    xdg_config = env_vars.get("XDG_CONFIG_HOME")
    if xdg_config:
        dirs.append(Path(xdg_config) / "3viz")
    else:
        dirs.append(Path.home() / ".config" / "3viz")

    # Legacy home directory
    dirs.append(Path.home() / ".3viz")

    return dirs


def is_3viz_conf_dir(path: Path) -> bool:
    """
    Check if a path is a 3viz configuration directory.

    Args:
        path: Path to check

    Returns:
        True if the directory exists
    """
    return path.exists() and path.is_dir()


def discover_user_definitions(
    env_vars: Optional[Dict[str, str]] = None
) -> Dict[Path, List[Path]]:
    """
    Discover user adapter definition files.

    Args:
        env_vars: Environment variables for testing

    Returns:
        Dict mapping config directories to their definition files
    """
    discovered = {}

    # Files to exclude from adapter discovery
    excluded_names = {"config", "3viz", "settings", "preferences"}

    for config_dir in get_user_config_dirs(env_vars):
        if is_3viz_conf_dir(config_dir):
            # Look for adapter definitions
            adapter_files = []

            # Check adapters subdirectory
            adapters_dir = config_dir / "adapters"
            if adapters_dir.exists():
                for ext in [".yaml", ".yml", ".json"]:
                    adapter_files.extend(adapters_dir.glob(f"*{ext}"))

            # Also check root directory for backward compatibility
            # but exclude config files
            for ext in [".yaml", ".yml", ".json"]:
                for file in config_dir.glob(f"*{ext}"):
                    if file.stem.lower() not in excluded_names:
                        adapter_files.append(file)

            if adapter_files:
                discovered[config_dir] = adapter_files

    return discovered


def list_user_definitions(
    env_vars: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    List all user configuration directories and their definition files.

    Args:
        env_vars: Environment variables for testing (default: os.environ)

    Returns:
        Dict with 'directories' and 'definitions' keys containing discovery results
    """
    config_dirs = get_user_config_dirs(env_vars)
    discovered = discover_user_definitions(env_vars)

    # Build directory status list
    directories = []
    for config_dir in config_dirs:
        if config_dir in discovered:
            status = "found"
            file_count = len(discovered[config_dir])
        elif is_3viz_conf_dir(config_dir):
            status = "found_no_definitions"
            file_count = 0
        else:
            status = "not_found"
            file_count = 0

        directories.append(
            {
                "path": str(config_dir),
                "status": status,
                "file_count": file_count,
            }
        )

    # Build definitions list
    definitions = []
    for config_dir, files in discovered.items():
        for file_path in files:
            definitions.append(
                {
                    "name": file_path.stem,
                    "file_path": str(file_path),
                    "config_dir": str(config_dir),
                    "format": file_path.suffix.lower(),
                }
            )

    return {
        "directories": directories,
        "definitions": definitions,
    }


def validate_user_definitions(
    env_vars: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Validate all user definition files and return results.

    Args:
        env_vars: Environment variables for testing (default: os.environ)

    Returns:
        Dict with 'valid_definitions', 'invalid_definitions', and 'summary' keys
    """
    discovered = discover_user_definitions(env_vars)

    valid_definitions = []
    invalid_definitions = []

    for config_dir, files in discovered.items():
        for file_path in files:
            try:
                # Try to load and parse the definition file
                import json
                from ruamel.yaml import YAML

                content = file_path.read_text()

                if file_path.suffix.lower() == ".json":
                    definition_dict = json.loads(content)
                else:  # yaml
                    yaml = YAML()
                    definition_dict = yaml.load(content)

                # Try to create an AdapterDef from it (validates structure)
                if isinstance(definition_dict, dict):
                    # Basic validation - check if it has some adapter-like fields
                    AdapterDef.from_dict(definition_dict)

                    valid_definitions.append(
                        {
                            "name": file_path.stem,
                            "file_path": str(file_path),
                            "config_dir": str(config_dir),
                            "format": file_path.suffix.lower(),
                        }
                    )
                else:
                    raise ValueError("Definition must be a dictionary")

            except Exception as e:
                invalid_definitions.append(
                    {
                        "name": file_path.stem,
                        "file_path": str(file_path),
                        "config_dir": str(config_dir),
                        "format": file_path.suffix.lower(),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

    # Summary statistics
    total_files = len(valid_definitions) + len(invalid_definitions)
    summary = {
        "total_files": total_files,
        "valid_count": len(valid_definitions),
        "invalid_count": len(invalid_definitions),
        "success_rate": (
            len(valid_definitions) / total_files if total_files > 0 else 1.0
        ),
    }

    return {
        "valid_definitions": valid_definitions,
        "invalid_definitions": invalid_definitions,
        "summary": summary,
    }
