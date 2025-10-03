"""
YAML utilities for treeviz definitions.

This module provides utilities for serializing definitions to YAML 
with comments extracted from dataclass field metadata using ruamel.yaml.
"""

from typing import Dict, Any
from dataclasses import asdict, fields, is_dataclass
from io import StringIO

try:
    from ruamel import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def get_dataclass_field_docs(dataclass_obj: Any) -> Dict[str, str]:
    """
    Extract field documentation from any dataclass metadata.

    Args:
        dataclass_obj: Any dataclass instance or class

    Returns:
        Dictionary mapping field names to their documentation strings
    """
    if not is_dataclass(dataclass_obj):
        return {}

    field_docs = {}
    for field_obj in fields(dataclass_obj):
        if field_obj.metadata and "doc" in field_obj.metadata:
            field_docs[field_obj.name] = field_obj.metadata["doc"]
    return field_docs


def serialize_dataclass_to_yaml(
    dataclass_obj: Any, include_comments: bool = True
) -> str:
    """
    Serialize any dataclass to YAML with optional field comments using ruamel.yaml.

    Args:
        dataclass_obj: Any dataclass instance to serialize
        include_comments: Whether to include field documentation as comments

    Returns:
        YAML string with optional comments

    Raises:
        ImportError: If ruamel.yaml is not available
        ValueError: If input is not a dataclass
    """
    if not is_dataclass(dataclass_obj):
        raise ValueError("Input must be a dataclass instance")

    return serialize_dict_to_yaml(
        asdict(dataclass_obj),
        include_comments=include_comments,
        field_docs=(
            get_dataclass_field_docs(dataclass_obj)
            if include_comments
            else None
        ),
    )


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
