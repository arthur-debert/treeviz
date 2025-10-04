# 3viz User Guide

3viz is a terminal-based visualizer for document Abstract Syntax Trees (ASTs). It transforms complex tree structures into readable, line-based visual representations that make understanding document structure intuitive.

## Core Concepts

### Adapters

Adapters are the bridge between your document format and 3viz's visualization. They define how to extract information from your specific AST format and map it to 3viz's universal node structure.

3viz comes with built-in adapters for common formats:
- mdast (Markdown)
- unist (Universal Syntax Tree)
- pandoc (Pandoc JSON)
- restructuredtext (docutils)

### Definitions

A definition is a configuration that tells 3viz how to interpret nodes in your tree. It specifies:
- How to extract node labels (the text displayed)
- How to find children nodes
- How to determine node types
- Icon mappings for visual clarity
- Type-specific overrides for different node types

### Visual Elements

Each line in 3viz output represents one node and includes:
- Icon (Unicode character representing node type)
- Label (descriptive text from the node)
- Metadata (additional attributes like type=ordered)
- Line count (how many lines this content spans)
- Indentation showing tree hierarchy

## Basic Usage

### Command Line

Process a document with a built-in adapter:

```bash
$ 3viz document.md mdast
```

Use a custom adapter definition:

```bash
$ 3viz document.json my-adapter.yaml
```

### Library Usage

```python
from threeviz import threeviz

# Using built-in adapter
result = threeviz.render("document.md", "mdast")
print(result)

# Using custom definition
custom_def = {
    "type": "nodeType", 
    "label": "text",
    "children": "children"
}
result = threeviz.render(document_data, custom_def)
```

## Custom Adapters

For formats not covered by built-in adapters, you can create custom definitions. A simple field mapping example:

```yaml
# my-format.yaml
type: "node_type"      # Field containing node type
label: "content"       # Field containing display text  
children: "child_nodes" # Field containing child array

icons:
  section: "§"
  paragraph: "¶"
  
type_overrides:
  title:
    label: "heading_text"  # Use different field for titles
```

This handles cases where your AST uses different field names than the defaults.

## Examples

### Processing Markdown

```bash
$ 3viz README.md mdast
```

Output shows document structure with appropriate icons and indentation.

### Custom Definition

For a simple JSON tree where nodes have 'kind' instead of 'type':

```python
definition = {
    "type": "kind",
    "label": "text", 
    "children": "children"
}
```

## Learn More

- [Visual Output Guide](theui.md) - Understanding the display format
- [Adapters Documentation](adapters.md) - Creating complex adapters
- [Adapter Walkthrough](adapter-walkthrough.md) - Step-by-step examples