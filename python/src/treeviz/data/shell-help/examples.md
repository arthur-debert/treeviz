# Examples

Here are practical examples of using 3viz with different types of ASTs and scenarios.

## Working with MDAST (Markdown)

```bash
# Basic markdown visualization
echo '{"type": "root", "children": [{"type": "heading", "depth": 1, "children": [{"type": "text", "value": "Hello World"}]}]}' | 3viz - mdast

# Output formats comparison
3viz markdown.json mdast --output-format term
3viz markdown.json mdast --output-format json  
3viz markdown.json mdast --output-format yaml
```

## Custom Adapter Example

Create a simple adapter for JavaScript ASTs:

**js-adapter.json:**

```json
{
  "label": "name",
  "type": "type",
  "children": "body", 
  "icons": {
    "Program": "📄",
    "FunctionDeclaration": "ƒ",
    "VariableDeclaration": "𝑥",
    "BinaryExpression": "⊕",
    "Identifier": "🏷"
  }
}
```

**Usage:**

```bash
3viz ast.json js-adapter.json --output-format term
```

## Pipeline Processing

```bash
# Extract function names from JavaScript AST
3viz ast.json js-adapter.json --output-format json | \
  jq -r '.. | select(.type? == "FunctionDeclaration") | .label'

# Count node types
3viz document.json --output-format json | \
  jq -r '.. | .type? // empty' | sort | uniq -c
```
