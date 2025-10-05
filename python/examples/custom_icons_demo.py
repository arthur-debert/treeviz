#!/usr/bin/env python3
"""
Demonstration of customizing icons in treeviz adapter definitions.

This example shows how to:
1. Override specific type icons
2. Create and register custom icon packs
3. Use icon packs in adapter definitions
"""

import json
from treeviz import render, Adapter


# Example 1: Simple icon customization
# Users can override icons for specific types
def demo_simple_icon_override():
    print("=== Example 1: Simple Icon Override ===\n")

    # Create custom adapter with overridden icons
    custom_adapter = Adapter(
        label="name",
        type="type",
        children="children",
        icons={
            "document": "📄",  # Use emoji instead of default ⧉
            "folder": "📁",  # Custom icon for folder type
            "file": "📃",  # Custom icon for file type
            "code": "💻",  # Custom icon for code
            "data": "📊",  # Custom icon for data files
        },
    )

    # Sample data structure
    tree_data = {
        "name": "My Project",
        "type": "folder",
        "children": [
            {
                "name": "src",
                "type": "folder",
                "children": [
                    {"name": "main.py", "type": "code"},
                    {"name": "utils.py", "type": "code"},
                ],
            },
            {
                "name": "data",
                "type": "folder",
                "children": [
                    {"name": "sales.csv", "type": "data"},
                    {"name": "report.json", "type": "data"},
                ],
            },
            {"name": "README.md", "type": "file"},
        ],
    }

    # Render with custom icons
    result = render(tree_data, custom_adapter, "text")
    print(result)
    print()


# Example 2: Using icon packs for themed icons
def demo_icon_packs():
    print("=== Example 2: Icon Packs for Themed Icons ===\n")

    # Define an icon pack for a developer-focused view
    developer_icons = {
        "python": "🐍",
        "javascript": "🟨",
        "typescript": "🔷",
        "rust": "🦀",
        "go": "🐹",
        "java": "☕",
        "config": "⚙️",
        "test": "🧪",
        "docs": "📚",
    }

    # Create adapter that uses the icon pack
    dev_adapter = Adapter(
        label="filename",
        type="language",
        children="files",
        icons=developer_icons,
    )

    # Project structure with language types
    project = {
        "filename": "awesome-project",
        "language": "folder",
        "files": [
            {"filename": "main.py", "language": "python"},
            {"filename": "test_main.py", "language": "test"},
            {"filename": "index.js", "language": "javascript"},
            {"filename": "app.ts", "language": "typescript"},
            {"filename": "server.go", "language": "go"},
            {"filename": "README.md", "language": "docs"},
            {"filename": "config.yaml", "language": "config"},
        ],
    }

    result = render(project, dev_adapter, "text")
    print(result)
    print()


# Example 3: Complex adapter with icon packs in YAML/JSON format
def demo_adapter_definition_with_icon_packs():
    print("=== Example 3: Full Adapter Definition with Icon Packs ===\n")

    # This is how a user would define a complete adapter with icon packs
    # This can be saved as a YAML or JSON file
    adapter_definition = {
        # Field mappings
        "label": "title",
        "type": "kind",
        "children": "items",
        # Custom icons for specific types
        "icons": {
            # Document structure icons
            "chapter": "📖",
            "section": "📑",
            "subsection": "📄",
            "paragraph": "¶",
            # Special content icons
            "warning": "⚠️",
            "info": "ℹ️",
            "tip": "💡",
            "important": "❗",
            "note": "📝",
            # Code and technical content
            "code": "💻",
            "example": "📋",
            "api": "🔌",
            "config": "⚙️",
        },
        # Type overrides for specific node types
        "type_overrides": {
            "code": {
                "label": "language",  # For code blocks, use 'language' field as label
            },
            "warning": {
                "label": "message",  # For warnings, use 'message' field
            },
        },
        # Ignore certain types
        "ignore_types": ["comment", "metadata"],
    }

    # Sample documentation structure
    doc_tree = {
        "title": "User Guide",
        "kind": "chapter",
        "items": [
            {
                "title": "Getting Started",
                "kind": "section",
                "items": [
                    {"title": "Installation", "kind": "subsection"},
                    {"title": "First Steps", "kind": "subsection"},
                    {"message": "Requires Python 3.8+", "kind": "warning"},
                ],
            },
            {
                "title": "Advanced Usage",
                "kind": "section",
                "items": [
                    {"language": "python", "kind": "code"},
                    {"title": "Best Practices", "kind": "tip"},
                    {"title": "Common Pitfalls", "kind": "important"},
                ],
            },
        ],
    }

    # Create adapter from definition
    doc_adapter = Adapter(**adapter_definition)

    # Render the documentation tree
    result = render(doc_tree, doc_adapter, "text")
    print(result)
    print()


# Example 4: Registering and using custom icon packs
def demo_register_icon_pack():
    print("=== Example 4: Registering Custom Icon Packs ===\n")

    from treeviz.icon_pack import register_icon_pack, Icon, IconPack

    # Create a custom icon pack for scientific/math content
    math_pack = IconPack(
        name="math_symbols",
        icons={
            "equation": Icon("∑", ["formula", "math"]),
            "matrix": Icon("⊞", ["array", "table"]),
            "vector": Icon("→", ["arrow"]),
            "integral": Icon("∫"),
            "derivative": Icon("∂"),
            "infinity": Icon("∞"),
            "pi": Icon("π"),
            "theta": Icon("θ"),
            "delta": Icon("Δ"),
            "sigma": Icon("σ"),
        },
    )

    # Register the icon pack
    register_icon_pack(math_pack)

    # Now use it in an adapter - the pack's icons are available
    math_adapter = Adapter(
        label="expression",
        type="math_type",
        children="terms",
        icons={
            "equation": "∑",  # From our math pack
            "variable": "x",
            "constant": "#",
            "operator": "⊕",
            "function": "ƒ",
        },
    )

    # Mathematical expression tree
    math_expr = {
        "expression": "∑(i²) for i in 1..n",
        "math_type": "equation",
        "terms": [
            {"expression": "i", "math_type": "variable"},
            {"expression": "²", "math_type": "operator"},
            {"expression": "sum", "math_type": "function"},
        ],
    }

    result = render(math_expr, math_adapter, "text")
    print(result)
    print()


# Example 5: Complete adapter saved as file
def demo_save_adapter_definition():
    print("=== Example 5: Saving Adapter Definition to File ===\n")

    # Users can save their adapter definitions as YAML or JSON files
    custom_adapter_def = {
        "label": "name",
        "type": "node_type",
        "children": "children",
        # Extensive icon customization
        "icons": {
            # File types
            "python": "🐍",
            "javascript": "📜",
            "typescript": "🔷",
            "json": "{ }",
            "yaml": "📋",
            "markdown": "📝",
            "text": "📄",
            # Folders and structure
            "folder": "📁",
            "package": "📦",
            "module": "🧩",
            # Special nodes
            "test": "🧪",
            "config": "⚙️",
            "docs": "📚",
            "data": "💾",
            "image": "🖼️",
            "video": "🎬",
            "audio": "🎵",
            # Status indicators
            "error": "❌",
            "warning": "⚠️",
            "success": "✅",
            "pending": "⏳",
            "locked": "🔒",
        },
        # Optional metadata
        "description": "Custom adapter for file system visualization",
        "version": "1.0.0",
        "author": "Your Name",
    }

    # Save as JSON
    with open("my_custom_adapter.json", "w") as f:
        json.dump(custom_adapter_def, f, indent=2)

    print("Adapter definition saved to my_custom_adapter.json")
    print("You can use it with: treeviz mydata.json my_custom_adapter.json")
    print("\nContents:")
    print(json.dumps(custom_adapter_def, indent=2)[:500] + "...")


if __name__ == "__main__":
    # Run all demonstrations
    demo_simple_icon_override()
    demo_icon_packs()
    demo_adapter_definition_with_icon_packs()
    demo_register_icon_pack()
    demo_save_adapter_definition()
