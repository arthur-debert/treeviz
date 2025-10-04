"""
Pure Python functions for user library management commands.

These functions implement the core logic for CLI commands, separate from 
output formatting to enable easy testing and reuse.
"""

from typing import Dict, Optional, Any

from .user_config import (
    get_user_config_dirs,
    is_3viz_conf_dir,
    discover_user_definitions,
)
from .lib import AdapterLib
from .model import AdapterDef


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
                # Try to load the definition file
                definition_dict = AdapterLib.load_definition_file(file_path)

                # Try to create an AdapterDef from it (validates structure)
                default_def = AdapterDef.default()
                default_def.merge_with(definition_dict)

                valid_definitions.append(
                    {
                        "name": file_path.stem,
                        "file_path": str(file_path),
                        "config_dir": str(config_dir),
                        "format": file_path.suffix.lower(),
                    }
                )

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
