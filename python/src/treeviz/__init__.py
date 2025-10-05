"""
3viz - Standalone AST Visualization Library

3viz transforms any tree structure into clean, scannable visualizations with minimal definition.
Designed for developers debugging parsers, analyzing ASTs, and understanding document structure.

Quick Start
-----------

Main API (99% of use cases):
    
    import treeviz
    
    # File + built-in adapter
    result = treeviz.render("doc.json", "mdast")
    
    # Python object + built-in adapter  
    result = treeviz.render({"type": "root", "children": []}, "mdast")
    
    # Custom adapter
    custom = treeviz.Adapter(label="name", children="kids")
    result = treeviz.render(my_ast_data, custom)
    
    # Get Node tree for advanced processing
    tree = treeviz.render("doc.json", "mdast", treeviz.OutputFormat.OBJ)
    
    # Terminal output with colors
    result = treeviz.render("doc.json", "mdast", treeviz.OutputFormat.TERM)

Built-in Adapters:
    
    # List available adapters
    adapters = treeviz.AdapterLib.list()
    
    # Get specific adapter
    mdast_adapter = treeviz.AdapterLib.get("mdast")
    result = treeviz.render(my_data, mdast_adapter)

Direct Node Construction:
    
    from treeviz import Node
    
    tree = Node(
        label="MyProject", 
        type="directory", 
        icon="📁",
        children=[
            Node(label="main.py", type="file", icon="🐍", content_lines=45)
        ]
    )
    
    print(treeviz.render(tree))

Custom Adapter Configuration:
    
    custom_adapter = treeviz.Adapter(
        label="name",           # Extract label from node.name
        type="node_type",       # Extract type from node.node_type  
        children="child_nodes", # Extract children from node.child_nodes
        icons={
            "function": "⚡",    # Map function type to symbol
            "class": "🏛"       # Map class type to symbol
        }
    )
    
    result = treeviz.render(my_ast_node, custom_adapter)

Core Concepts
-------------

Node Structure:
    The universal 3viz representation with these fields:
    - label: Display text (required)
    - type: Node type for icon mapping (optional)
    - icon: Explicit Unicode symbol (optional) 
    - content_lines: Number of lines represented (default: 1)
    - source_location: Line/column info from original source (optional)
    - extra: Extensible key-value data (optional)
    - children: Child nodes (optional)

Adapter Configuration:
    Adapt any tree using configuration objects:
    - label, type, children: Map source fields to Node fields
    - icons: Map types to Unicode symbols
    - type_overrides: Per-type attribute customization
    - ignore_types: Filter out unwanted node types

Output Formats:
    - OutputFormat.TEXT: Plain text (default)
    - OutputFormat.TERM: Terminal with colors/formatting
    - OutputFormat.JSON: JSON representation
    - OutputFormat.YAML: YAML representation
    - OutputFormat.OBJ: Return Node tree object

Error Handling:
    3viz follows "fail fast" principle - malformed input exits immediately
    with clear error messages rather than producing broken visualizations.

Built-in Adapters
-----------------

MDAST: For Markdown Abstract Syntax Trees
    treeviz.render(my_mdast, "mdast")

UNIST: For Universal Syntax Trees
    treeviz.render(my_unist, "unist")

3viz (default): For generic JSON/dict structures
    treeviz.render(my_data, "3viz")

See Also
--------

Examples: examples/standalone_3viz_demo.py
Tests: tests/treeviz/ for comprehensive usage examples
Advanced Features: Use lower-level APIs for complex path expressions,
    transformations, filtering, and custom rendering options

License: MIT
Repository: https://github.com/arthur-debert/treeviz
"""

# New primary public API
from .treeviz import (
    render,
    AdapterLib,
    OUTPUT_TEXT,
    OUTPUT_TERM,
    OUTPUT_JSON,
    OUTPUT_YAML,
    OUTPUT_OBJ,
)
from .definitions.model import AdapterDef as Adapter

# Core data structures
from .model import Node

# Legacy API (kept for backward compatibility, but not in primary docs)
from .adapters import (
    adapt_tree,
    adapt_node,
)
from .formats import (
    parse_document,
    Format,
    DocumentFormatError,
    register_format,
    get_supported_formats,
    get_format_by_name,
)
from .rendering import (
    render as render_nodes,
    create_render_options,
    RenderOptions,
    DEFAULT_SYMBOLS,
)

__version__ = "1.0.0"
__all__ = [
    # Primary API
    "render",
    "Adapter",
    "AdapterLib",
    # Output format constants
    "OUTPUT_TEXT",
    "OUTPUT_TERM",
    "OUTPUT_JSON",
    "OUTPUT_YAML",
    "OUTPUT_OBJ",
    # Core data structures
    "Node",
    # Legacy API (for backward compatibility)
    "adapt_tree",
    "adapt_node",
    "parse_document",
    "Format",
    "DocumentFormatError",
    "register_format",
    "get_supported_formats",
    "get_format_by_name",
    "render_nodes",
    "create_render_options",
    "RenderOptions",
    "DEFAULT_SYMBOLS",
]
