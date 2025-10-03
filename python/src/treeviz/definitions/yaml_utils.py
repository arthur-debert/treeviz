"""
YAML utilities for treeviz definitions.

This module provides utilities for serializing definitions to YAML 
with comments extracted from dataclass field metadata using ruamel.yaml.
"""

from typing import Dict, Any
from dataclasses import asdict
from io import StringIO

try:
    from ruamel import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .model import Definition


def serialize_definition_to_yaml(
    definition: Definition, include_comments: bool = True
) -> str:
    """
    Serialize a Definition to YAML with optional field comments using ruamel.yaml.

    Args:
        definition: The Definition object to serialize
        include_comments: Whether to include field documentation as comments

    Returns:
        YAML string with optional comments

    Raises:
        ImportError: If ruamel.yaml is not available
    """
    if not HAS_YAML:
        raise ImportError(
            "YAML support requires 'ruamel.yaml' package. Install with: pip install ruamel.yaml"
        )

    # Create YAML instance with proper configuration
    yml = yaml.YAML()
    yml.preserve_quotes = True
    yml.default_flow_style = False
    yml.indent(mapping=2, sequence=4, offset=2)

    # Convert to dict and create CommentedMap for comments
    def_data = asdict(definition)
    commented_data = yaml.CommentedMap(def_data)

    if include_comments:
        # Get field documentation
        field_docs = Definition.get_field_docs()

        # Add comments for each field that has documentation
        for field_name, doc in field_docs.items():
            if field_name in commented_data:
                # Add comment before the field
                commented_data.yaml_set_comment_before_after_key(
                    field_name, before=doc
                )

    # Serialize to string
    stream = StringIO()
    yml.dump(commented_data, stream)
    return stream.getvalue()


def serialize_dict_to_yaml(
    data: Dict[str, Any],
    include_comments: bool = False,
    field_docs: Dict[str, str] = None,
) -> str:
    """
    Serialize a dictionary to YAML with optional field comments.

    Args:
        data: Dictionary to serialize
        include_comments: Whether to include field documentation as comments
        field_docs: Optional field documentation mapping

    Returns:
        YAML string with optional comments

    Raises:
        ImportError: If ruamel.yaml is not available
    """
    if not HAS_YAML:
        raise ImportError(
            "YAML support requires 'ruamel.yaml' package. Install with: pip install ruamel.yaml"
        )

    # Create YAML instance
    yml = yaml.YAML()
    yml.preserve_quotes = True
    yml.default_flow_style = False
    yml.indent(mapping=2, sequence=4, offset=2)

    if not include_comments or not field_docs:
        # Simple serialization without comments
        stream = StringIO()
        yml.dump(data, stream)
        return stream.getvalue()

    # Create CommentedMap and add comments
    commented_data = yaml.CommentedMap(data)

    for field_name, doc in field_docs.items():
        if field_name in commented_data:
            commented_data.yaml_set_comment_before_after_key(
                field_name, before=doc
            )

    stream = StringIO()
    yml.dump(commented_data, stream)
    return stream.getvalue()
