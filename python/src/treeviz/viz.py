from treeviz.adapters import convert_document, load_adapter
from treeviz.formats import load_document
from treeviz.rendering import TemplateRenderer


import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union


def generate_viz(
    document_path: Union[str, Path, Dict, list, Any],
    adapter_spec: Union[str, Dict, Any] = "3viz",
    document_format: Optional[str] = None,
    adapter_format: Optional[str] = None,
    output_format: str = "term",
    terminal_width: Optional[int] = 80,
    theme: Optional[str] = None,
    presentation: Optional[Union[str, Path]] = None,
) -> Union[str, Any]:
    """
    Generate 3viz visualization from document.

    Main orchestration function that coordinates document loading, adapter loading,
    conversion, and rendering. Supports both file paths and Python objects.

    Args:
        document_path: Path to document file, '-' for stdin, or Python object (dict/list/Node)
        adapter_spec: Adapter name, file path, or adapter dict/object (default: "3viz")
        document_format: Override document format detection (default: auto-detect)
        adapter_format: Override adapter format detection (default: auto-detect)
        output_format: Output format - json/yaml/text/term/obj (default: "term")
        terminal_width: Terminal width for text/term output (default: 80)
        theme: Theme override - 'dark' or 'light' (default: auto-detect)
        presentation: Path to presentation.yaml configuration file

    Returns:
        String output in the specified format, or Node object if output_format="obj"

    Raises:
        Various exceptions from sub-functions (DocumentFormatError, ValueError, etc.)
    """
    # Load the document
    document = load_document(document_path, format_name=document_format)

    # Load the adapter definition (icons are now in style)
    adapter_def, _ = load_adapter(adapter_spec, adapter_format=adapter_format)

    # Convert document to 3viz Node format
    node = convert_document(document, adapter_def)

    # Handle output format
    if output_format == "obj":
        # For obj output, return Node object directly
        return node
    elif output_format in ["json", "yaml"]:
        # For data formats, convert Node to dict and serialize
        if node is None:
            result_data = None
        else:
            result_data = asdict(node)

        if output_format == "json":
            return json.dumps(result_data, indent=2, ensure_ascii=False)
        else:  # yaml
            try:
                from .definitions.yaml_utils import serialize_dataclass_to_yaml

                if node is None:
                    return "null\n"
                return serialize_dataclass_to_yaml(node, include_comments=False)
            except ImportError:
                # Fallback to JSON if YAML not available
                return json.dumps(result_data, indent=2, ensure_ascii=False)

    elif output_format in ["text", "term"]:
        # For text/term formats, use the new template renderer
        if node is None:
            return ""  # Empty output for ignored nodes

        # Use provided terminal width or default
        if terminal_width is None:
            terminal_width = 80

        # Create renderer and presentation
        renderer = TemplateRenderer()
        from pathlib import Path

        from .rendering import Presentation, PresentationLoader

        # Load presentation configuration
        if presentation:
            loader = PresentationLoader()
            presentation_obj = loader.load_presentation_hierarchy(
                Path(presentation)
            )
        else:
            # Create default presentation
            presentation_obj = Presentation()

        # Apply theme override if specified
        if theme:
            presentation_obj.theme_name = theme
            # Reload the theme
            from .config.loaders import create_config_loaders

            loaders = create_config_loaders()
            theme_obj = loaders.load_theme(theme)
            if theme_obj:
                presentation_obj.theme = theme_obj

        # Override terminal width if specified
        if terminal_width:
            presentation_obj.view.max_width = terminal_width

        return renderer.render(node, presentation_obj)

    else:
        raise ValueError(f"Unknown output format: {output_format}")
