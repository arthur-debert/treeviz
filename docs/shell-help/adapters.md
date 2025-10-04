# Adapters

Adapters are configuration files that tell 3viz how to interpret different AST formats. They provide a mapping between the source format and 3viz's internal representation.

## How Adapters Work

An adapter defines:
- **Field mappings**: Which fields contain labels, types, children, etc.
- **Icon mappings**: Visual icons for different node types
- **Type overrides**: Special handling for specific node types
- **Filtering**: Which node types to ignore during processing

## Built-in Adapters

**3viz**: The native format, no adaptation needed
- Direct mapping to 3viz Node structure
- Supports all 3viz features out of the box

**mdast**: Markdown Abstract Syntax Tree
- Maps markdown elements to visual representations
- Handles headings, paragraphs, lists, code blocks, etc.
- Icons: ⧉ (root), ⊤ (heading), ¶ (paragraph), 𝒱 (code)

**unist**: Universal Syntax Tree
- Generic adapter for Unist-based formats
- Minimal mapping suitable for many tree formats

## Custom Adapters

Create JSON or YAML files with adapter definitions:

```json
{
  "label": "name",
  "type": "type", 
  "children": "body",
  "icons": {
    "function": "ƒ",
    "class": "⊙",
    "variable": "𝑥"
  }
}
```

Save as `my-adapter.json` and use with:
```bash
3viz document.ast my-adapter.json
```