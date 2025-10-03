"""
3viz - Standalone AST Visualization Library

3viz transforms any tree structure into clean, scannable visualizations with minimal definition.
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

    from treeviz import adapt_node
    
    def_ = {
        "attributes": {
            "label": "name",           # Extract label from node.name
            "type": "node_type",       # Extract type from node.node_type  
            "children": "child_nodes"  # Extract children from node.child_nodes
        },
        "icons": {
            "function": "⚡",           # Map function type to symbol
            "class": "🏛"              # Map class type to symbol
        }
    }
    
    result = adapt_node(my_ast_node, def_)

Built-in Format Support:

    from treeviz import adapt_node
    
    # Use pre-built definition for MDAST structures  
    from dataclasses import asdict
    from treeviz.definitions import Lib
    def_ = asdict(Lib.get("mdast"))
    result = adapt_node(my_mdast_tree, def_)
    
    # For JSON/dict structures, use default definition (baseline icons work automatically)
    from treeviz.definitions import Definition
    def_ = asdict(Definition.default())  # Returns default definition with baseline icons
    result = adapt_node({"name": "test", "items": [1, 2, 3]}, def_)

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
    Adapt any tree using JSON definition instead of custom code:
    - attributes: Map source fields to Node fields
    - icons: Map types to Unicode symbols
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

MDAST: For Markdown Abstract Syntax Trees
    
    from treeviz.definitions import Lib
    def_ = asdict(Lib.get("mdast"))
    # Handles paragraph, heading, list, text nodes with proper icons

UNIST: For Universal Syntax Trees
    
    def_ = asdict(Lib.get("unist"))
    # Handles element, text, comment nodes with proper element rendering

Generic JSON/Dict Structures:
    
    from treeviz.definitions import Definition
    def_ = asdict(Definition.default())  # Returns baseline definition
    # Baseline icons automatically handle dict, array, str, int, bool, etc.

Error Messages
--------------

Common issues and solutions:

KeyError: "Configuration must include 'attributes' section"
    → Add attributes mapping: {"attributes": {"label": "name"}}

TypeError: "Children attribute must return a list, got str"  
    → Check that children path points to list, not string

AttributeError: "Failed to extract attribute 'missing_field'"
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

Test definitions interactively:
    
    from treeviz.definitions.schema import Definition
    try:
        Definition.from_dict(my_def)
        print("Configuration valid!")
    except (TypeError, KeyError, ValueError) as e:
        print(f"Definition error: {e}")

Generate sample definitions:
    
    # Option 1: Dictionary format (classic)
    sample_def = {
        "attributes": {"label": "name", "type": "node_type"},
        "icons": {"function": "⚡", "class": "🏛"}
    }
    
    # Option 2: Dataclass format (recommended - typed and validated)
    from treeviz.definitions import Definition
    from dataclasses import asdict
    sample_def = asdict(Definition(
        attributes={"label": "name", "type": "node_type"},
        icons={"function": "⚡", "class": "🏛"}
    ))

See Also
--------

Examples: examples/standalone_3viz_demo.py
Tests: tests/treeviz/ for comprehensive usage examples
def_ Reference: treeviz.definitions module for detailed definition options
Converter Reference: treeviz.adapters module for advanced extraction features

License: MIT
Repository: https://github.com/arthur-debert/treeviz/tree/main/src/treeviz
"""

# Main public API exports
from .model import Node
from .adapters import (
    adapt_tree,
    adapt_node,
)

# Document format parsing
from .formats import (
    parse_document,
    Format,
    DocumentFormatError,
    register_format,
    get_supported_formats,
    get_format_by_name,
)

# No custom exceptions - we use standard Python exceptions with helpful messages
from .renderer import (
    render,
    create_render_options,
    RenderOptions,
    DEFAULT_SYMBOLS,
)

__version__ = "1.0.0"
__all__ = [
    # Core data structures
    "Node",
    # Conversion engine
    "adapt_tree",
    "adapt_node",
    # Document format parsing
    "parse_document",
    "Format",
    "DocumentFormatError",
    "register_format",
    "get_supported_formats",
    "get_format_by_name",
    # Rendering
    "render",
    "create_render_options",
    "RenderOptions",
    "DEFAULT_SYMBOLS",
]
