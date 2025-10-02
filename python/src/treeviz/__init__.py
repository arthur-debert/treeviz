"""
3viz - Standalone AST Visualization Library

3viz transforms any tree structure into clean, scannable visualizations with minimal configuration.
Designed for developers debugging parsers, analyzing ASTs, and understanding document structure.

Quick Start
-----------

Direct Node Construction:
    
    from treeviz import Node, render
    
    tree = Node(
        label="MyProject", 
        type="directory", 
        icon="📁",
        children=[
            Node(label="main.py", type="file", icon="🐍", content_lines=45)
        ]
    )
    
    print(render(tree))

Declarative Conversion:

    from treeviz import convert_node
    
    config = {
        "attributes": {
            "label": "name",           # Extract label from node.name
            "type": "node_type",       # Extract type from node.node_type  
            "children": "child_nodes"  # Extract children from node.child_nodes
        },
        "icon_map": {
            "function": "⚡",           # Map function type to symbol
            "class": "🏛"              # Map class type to symbol
        }
    }
    
    result = convert_node(my_ast_node, config)

Built-in Format Support:

    from treeviz import get_builtin_config, convert_node
    
    # Use pre-built configuration for JSON structures
    config = get_builtin_config("json")
    result = convert_node({"name": "test", "items": [1, 2, 3]}, config)

Core Concepts
-------------

Node Structure:
    The universal 3viz representation with these fields:
    - label: Display text (required)
    - type: Node type for icon mapping (optional)
    - icon: Explicit Unicode symbol (optional) 
    - content_lines: Number of lines represented (default: 1)
    - source_location: Line/column info from original source (optional)
    - metadata: Extensible key-value data (optional)
    - children: Child nodes (optional)

Declarative Configuration:
    Convert any tree using JSON configuration instead of custom code:
    - attributes: Map source fields to Node fields
    - icon_map: Map types to Unicode symbols
    - type_overrides: Per-type attribute customization
    - ignore_types: Filter out unwanted node types

Error Handling:
    3viz follows "fail fast" principle - malformed input exits immediately
    with clear error messages rather than producing broken visualizations.

Advanced Features (Phase 2)
----------------------------

Complex Path Expressions:
    
    # Dot notation for nested access
    "label": "metadata.title"
    
    # Array indexing 
    "label": "children[0].name"
    
    # Complex paths with fallbacks
    "label": {"path": "title", "fallback": "name", "default": "Untitled"}

Conditional Extraction:
    
    # Different extraction based on node type
    "type_overrides": {
        "function": {
            "label": "name",
            "metadata": {"params": "parameters", "returns": "return_type"}
        },
        "class": {
            "label": {"path": "class_name", "transform": "capitalize"}
        }
    }

Transformation Functions:
    
    # Built-in transformations
    "label": {"path": "name", "transform": "upper"}
    "label": {"path": "content", "transform": "truncate", "max_length": 50}
    
    # Custom transformation functions
    "label": {"path": "items", "transform": lambda items: f"Count: {len(items)}"}

Filtering and Predicates:
    
    # Filter children based on conditions
    "children": {
        "path": "child_nodes",
        "filter": {"type": {"not_in": ["comment", "whitespace"]}}
    }
    
    # Complex filtering predicates  
    "children": {
        "path": "methods",
        "filter": {"visibility": "public", "name": {"startswith": "get_"}}
    }

Output Customization:
    
    # Custom symbols and terminal width
    from treeviz import render, create_render_options
    
    options = create_render_options(
        symbols={"custom_type": "⚙"},
        terminal_width=120
    )
    output = render(node, options)

Built-in Configurations
-----------------------

JSON: For JSON-like structures
    
    config = get_builtin_config("json")
    # Handles dicts, lists, and primitive types automatically

MDAST: For Markdown Abstract Syntax Trees
    
    config = get_builtin_config("mdast") 
    # Handles paragraph, heading, list, text nodes with proper text extraction

Error Messages
--------------

Common issues and solutions:

ConversionError: "Configuration must include 'attributes' section"
    → Add attributes mapping: {"attributes": {"label": "name"}}

ConversionError: "Children attribute must return a list, got str"  
    → Check that children path points to list, not string

ConversionError: "Failed to extract attribute 'missing_field'"
    → Verify field exists or add fallback/default values

Performance Guidelines
-----------------------

Optimal for ASTs with:
    - Up to ~100 nodes for visual clarity
    - Simple to moderate nesting depth
    - Text content under 1000 characters per node

For larger structures:
    - Use ignore_types to filter noise
    - Apply filtering predicates to reduce size
    - Consider processing subtrees independently

Development and Debugging
--------------------------

Enable detailed error messages:
    
    import logging
    logging.basicConfig(level=logging.DEBUG)

Test configurations interactively:
    
    from treeviz import validate_config, ConversionError
    try:
        validate_config(my_config)
        print("Configuration valid!")
    except ConversionError as e:
        print(f"Config error: {e}")

Generate sample configurations:
    
    # Create configurations manually using declarative syntax
    sample_config = {
        "attributes": {"label": "name", "type": "node_type"},
        "icon_map": {"function": "⚡", "class": "🏛"}
    }

See Also
--------

Examples: examples/standalone_3viz_demo.py
Tests: tests/treeviz/ for comprehensive usage examples
Config Reference: treeviz.config module for detailed configuration options
Converter Reference: treeviz.converter module for advanced extraction features

License: MIT
Repository: https://github.com/arthur-debert/treeviz/tree/main/src/treeviz
"""

# Main public API exports
from .model import Node
from .converter import (
    convert_tree,
    convert_node,
    validate_config,
)
from .exceptions import ConversionError
from .renderer import (
    render,
    create_render_options,
    RenderOptions,
    DEFAULT_SYMBOLS,
)
from .config import (
    load_config,
    get_builtin_config,
)

__version__ = "1.0.0"
__all__ = [
    # Core data structures
    "Node",
    # Conversion engine
    "convert_tree",
    "convert_node",
    "validate_config",
    "ConversionError",
    # Rendering
    "render",
    "create_render_options",
    "RenderOptions",
    "DEFAULT_SYMBOLS",
    # Configuration management
    "load_config",
    "get_builtin_config",
]
