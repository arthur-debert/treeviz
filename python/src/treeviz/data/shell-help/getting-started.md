# Getting Started with 3viz

3viz is a command-line tool for visualizing Abstract Syntax Trees (ASTs) in a readable, hierarchical format.

## Quick Start

**Basic Usage:**

```bash
# Visualize a JSON AST with default adapter
3viz document.json

# Use a specific adapter  
3viz document.json mdast

# Read from stdin
cat document.json | 3viz - mdast

# Output in different formats
3viz document.json --output-format yaml
```

**Common Workflows:**

1. **Exploring a new AST format**: Start with the default 3viz adapter to see the raw structure
2. **Using built-in adapters**: Try mdast for Markdown or unist for generic trees  
3. **Creating custom adapters**: Define field mappings for your specific AST format
4. **Processing output**: Use JSON/YAML formats for further analysis

## What You'll See

3viz shows your AST as an indented tree with:

- Visual icons for different node types
- Content size indicators (line counts)
- Hierarchical structure through indentation
- Node labels and metadata

## Next Steps

- `3viz help adapters` - Learn about adapters and format mapping
- `3viz help 3viz-output` - Understand output formats and structure
- `3viz get-definition mdast` - See adapter definitions
