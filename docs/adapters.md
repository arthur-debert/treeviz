# Adapter Definition System

The 3viz adapter definition system provides a declarative approach to transforming Abstract Syntax Trees (ASTs) from various document formats into a standardized tree visualization format. This system allows complex document structures to be processed without writing custom code, using only configuration files.

## Overview

Adapters define how to extract and transform data from source AST nodes into 3viz's normalized node format. The system supports three main approaches:

1. **Simple Field Mapping** - Direct field-to-field extraction
2. **Transform Pipelines** - Multi-step data processing chains
3. **Collection Synthesis** - Creating new node structures from raw data

## Schema Reference

### Core Adapter Definition

```python
@dataclass
class AdapterDef:
    # Basic field mappings
    label: Any = "label"           # How to extract node labels
    type: str = "type"             # Field containing node type
    children: Any = "children"     # How to extract children
    icon: Any = None               # Icon field or type-based mapping
    content_lines: Any = 1         # Lines field or fixed number
    source_location: Any = None    # Source location information
    extra: Any = {}               # Extra metadata extraction
    
    # Advanced configuration
    icons: Dict[str, str] = field(default_factory=dict)
    type_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    ignore_types: List[str] = field(default_factory=list)
```

### Basic Field Extraction

The simplest form specifies field names as strings:

```yaml
# Simple field mapping
label: "content"        # Extract label from node.content
type: "nodeType"        # Extract type from node.nodeType  
children: "childNodes"  # Extract children from node.childNodes
```

### Advanced Extraction Specifications

For complex data structures, use extraction specifications with path expressions, transforms, and fallbacks:

```yaml
label:
  path: "content.text"           # Path to nested field
  transform:                     # Processing pipeline
    - name: "truncate"
      max_length: 50
  default: "Unknown"             # Fallback value
```

## Path Expressions

Path expressions provide powerful data access patterns:

### Basic Syntax

```yaml
# Simple field access
path: "title"

# Nested field access
path: "metadata.title"

# Array indexing
path: "items[0]"

# Mixed nested access
path: "content[1].text.value"
```

### Complex Examples

```yaml
# Extract language from deeply nested structure
path: "c[0][1][0]"              # CodeBlock language in Pandoc

# Get first child's content
path: "children[0].content"

# Access nested metadata
path: "frontmatter.meta.author"
```

## Transform Pipelines

Transform pipelines enable sophisticated data processing through sequential operations:

### Pipeline Structure

```yaml
label:
  path: "source_field"
  transform:
    - name: "operation1"
      param1: value1
    - name: "operation2" 
      param2: value2
  default: "fallback_value"
```

### Available Transforms

#### Text Transforms
- **upper** - Convert to uppercase
- **lower** - Convert to lowercase  
- **capitalize** - Capitalize first letter
- **strip** - Remove whitespace
- **truncate** - Limit text length with suffix
- **prefix** - Add text prefix

```yaml
transform:
  - name: "truncate"
    max_length: 60
    suffix: "..."
  - name: "prefix"
    prefix: "H"
```

#### Collection Transforms
- **filter** - Keep items matching conditions
- **extract** - Extract field from each item
- **join** - Combine items into string
- **first/last** - Get first/last item
- **length** - Get collection size
- **flatten** - Flatten nested lists

```yaml
transform:
  - name: "filter"          # Keep only String nodes
    t: "Str"
  - name: "extract"         # Extract 'c' field from each
    field: "c"
  - name: "join"            # Join with spaces
    separator: " "
```

#### Numeric Transforms
- **abs** - Absolute value
- **round** - Round to decimals
- **format** - Format with spec

#### Type Conversions
- **str** - Convert to string
- **int** - Convert to integer
- **float** - Convert to float

### Pipeline Examples

#### Text Extraction and Processing
```yaml
# Extract text from nested structure, clean and truncate
label:
  path: "content"
  transform:
    - name: "filter"
      type: "text"
    - name: "extract" 
      field: "value"
    - name: "join"
      separator: " "
    - name: "strip"
    - name: "truncate"
      max_length: 60
      suffix: "..."
  default: "Empty"
```

#### Numeric Processing
```yaml
# Process numeric data with formatting
content_lines:
  path: "stats.lineCount"
  transform:
    - name: "abs"
    - name: "round"
      digits: 0
    - name: "int"
  default: 1
```

## Collection Mapping

Collection mapping transforms raw arrays into structured nodes, enabling synthesis of new node types:

### Basic Mapping

```yaml
children:
  path: "items"              # Source array
  map:
    template:                # Template for new nodes
      t: "ListItem"         # Set type field
      content: "${item}"    # Reference to current item
    variable: "item"         # Variable name (default: "item")
```

### Template Variables

Templates support placeholder expressions with path access:

```yaml
map:
  template:
    type: "ProcessedItem"
    label: "${item.title}"           # Simple field access
    content: "${item.data.text}"     # Nested field access
    index: "${item.meta.position[0]}" # Array access
```

### Advanced Mapping Examples

#### Pandoc List Processing
```yaml
# Transform Pandoc list items with complex structure
children:
  path: "c"                  # Raw list items
  map:
    template:
      t: "ListItem"
      text: "${item[0].c[0].c}"     # Direct path to text
      original: "${item}"           # Keep original structure
```

#### Nested Document Processing  
```yaml
# Process nested document sections
children:
  path: "sections"
  map:
    template:
      type: "Section"
      title: "${item.heading.text}"
      level: "${item.heading.level}"
      content: "${item.body}"
```

## Type Overrides

Type overrides specify different extraction rules for specific node types:

```yaml
type_overrides:
  # Document root has different structure
  Document:
    children: "body"
    label: "Document Root"
    
  # Headers have complex label generation  
  Header:
    children: "content"
    label:
      path: "content"
      transform:
        - name: "filter"
          type: "text"
        - name: "extract"
          field: "value"
        - name: "join"
          separator: " "
        - name: "prefix"
          prefix: "H"
    
  # Code blocks are leaf nodes
  CodeBlock:
    children: []
    label:
      path: "lang"
      transform:
        - name: "prefix"
          prefix: "CodeBlock("
        - name: "suffix"
          suffix: ")"
      default: "CodeBlock"
```

## Children Selection

### Simple Field Access
```yaml
children: "childNodes"      # Extract from field
```

### Node-Based Filtering
```yaml
children:
  include: ["*"]            # Include all types (default)
  exclude: ["Space", "Comment"]  # Exclude specific types
```

### Advanced Children Processing
```yaml
children:
  path: "content"           # Source field
  transform:                # Process before creating children
    - name: "filter"
      valid: true
  map:                      # Transform items into nodes
    template:
      type: "Child"
      data: "${item}"
```

## Icons and Visual Elements

### Type-Based Icons
```yaml
icons:
  Document: "📄"
  Header: "H"
  Paragraph: "¶"
  CodeBlock: "```"
  List: "•"
  Link: "🔗"
```

### Dynamic Icons
```yaml
# Icons can be extracted from data
icon:
  path: "metadata.icon"
  default: "📄"
```

## Configuration Options

### Ignore Types
```yaml
ignore_types:
  - "Space"         # Whitespace nodes
  - "Comment"       # Comment nodes  
  - "SoftBreak"     # Soft line breaks
```

### Content Lines
```yaml
# Static value
content_lines: 1

# Dynamic extraction
content_lines:
  path: "lineCount"
  default: 1
```

### Source Location
```yaml
source_location:
  path: "position"
  transform:
    - name: "format"
      format_spec: "line {line}, col {column}"
```

## Advanced Patterns

### Conditional Processing
```yaml
# Use fallback paths for robustness
label:
  path: "title"
  fallback: "name"          # Try 'name' if 'title' fails
  default: "Untitled"       # Final fallback
```

### Multi-Step Extraction
```yaml
# Complex header processing
label:
  path: "content"
  transform:
    - name: "filter"          # First, filter to text nodes
      type: "text"
    - name: "extract"         # Extract text content
      field: "value"
    - name: "join"            # Combine text pieces
      separator: " "
    - name: "truncate"        # Limit length
      max_length: 50
    - name: "prefix"          # Add type indicator
      prefix: "Header: "
  default: "Header"
```

### Data Synthesis
```yaml
# Create rich metadata
extra:
  path: "."                 # Start with entire node
  transform:
    - name: "extract_metadata"  # Custom transform
      fields: ["id", "class", "data-*"]
```

## Error Handling

The system provides robust error handling:

- **Graceful Fallbacks** - Use `default` values when extraction fails
- **Path Validation** - Warns about malformed path expressions
- **Type Safety** - Validates transform parameters
- **Debug Logging** - Detailed extraction logs for troubleshooting

### Example Error Handling
```yaml
label:
  path: "content.title"     # Primary extraction
  fallback: "name"          # Fallback if primary fails
  default: "Unknown"        # Final fallback
  transform:
    - name: "truncate"
      max_length: 100       # Prevent overly long labels
```

## File Formats

Adapters can be defined in multiple formats:

### YAML Format (Recommended)
```yaml
# Clean, readable format for complex definitions
type: "nodeType"
children: "childNodes"
type_overrides:
  Header:
    label:
      path: "content"
      transform: [...]
```

### JSON Format
```json
{
  "type": "nodeType",
  "children": "childNodes", 
  "icons": {
    "header": "H",
    "paragraph": "¶"
  }
}
```

### Python Format (For Complex Logic)
```python
# For cases requiring custom functions
definition = {
    "type": "nodeType",
    "label": lambda node: complex_label_logic(node),
    "children": lambda node: filter_children(node)
}
```

## Best Practices

1. **Start Simple** - Begin with basic field mappings, add complexity as needed
2. **Use Transforms** - Prefer transform pipelines over custom functions
3. **Handle Errors** - Always provide fallbacks and defaults
4. **Test Thoroughly** - Test with various input structures
5. **Document Intent** - Use comments to explain complex extraction logic
6. **Performance** - Consider caching for expensive transformations

## Examples Repository

See `docs/adapter-walkthrough.md` for a detailed walkthrough of the Pandoc adapter, which demonstrates all these features in practice on a real-world complex AST format.