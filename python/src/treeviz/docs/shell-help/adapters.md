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

Type overrides specify different extraction rules for specific node types and can even change the node type itself:

### Basic Type Overrides

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

### Advanced Type Transformation

Type overrides can transform node types for challenging AST formats:

```yaml
# Handle inconsistent type fields
type:
  path: "t"                   # Primary type field
  fallback: "nodeType"        # Alternative field name
  default: "Unknown"          # Fallback for missing types

type_overrides:
  # Transform fallback types into meaningful ones
  Unknown:
    type: "Document"          # Override the type itself
    children: "blocks"        # Use different children field
    label: "Document Root"    # Provide meaningful label
    
  # Handle format variations
  LegacyNode:
    type: "ModernNode"        # Transform to new type system
    children: 
      path: "content"
      fallback: "body"        # Support multiple format versions
```

### Type Override Features

- **Type Transformation**: Change `Unknown` → `Document`
- **Field Remapping**: Override any extraction pattern
- **Icon Resolution**: Icons use the final transformed type
- **Backward Compatibility**: Support multiple format versions

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

## Challenging AST Format Patterns

The declarative system includes sophisticated patterns for handling problematic AST structures without custom code:

### 1. Inconsistent Root Nodes

Many AST formats have root nodes that don't follow the same patterns as other nodes.

**Problem**: Root lacks type field or uses different structure:

```json
{
  "pandoc-api-version": [1, 23, 1],
  "meta": {},
  "blocks": [...],  // ← No 't' field, children in 'blocks' not 'c'
}
```

**Solution**: Use type defaults and overrides:

```yaml
type:
  path: "t"
  default: "Unknown"          # Fallback when 't' missing

type_overrides:
  Unknown:
    type: "Document"          # Transform Unknown → Document
    children: "blocks"        # Override children field
    label: "Document Root"    # Meaningful label
```

### 2. Missing or Inconsistent Type Fields

**Problem**: Different nodes use different type field names or lack them entirely.

**Solution**: Multi-level fallback strategy:

```yaml
type:
  path: "type"              # Try primary field
  fallback: "nodeType"      # Try alternative field
  default: "GenericNode"    # Final fallback

type_overrides:
  GenericNode:
    type: "ProcessedNode"   # Give meaningful type
    label:
      path: "name"
      fallback: "id"
      default: "Unnamed"
```

### 3. Deeply Nested Critical Information

**Problem**: Important data buried deep in nested structures.

**Solution**: Complex path navigation with fallbacks:

```yaml
type_overrides:
  ComplexNode:
    label:
      path: "data.meta.display.title"     # Primary deep path
      fallback: "attributes.name"         # Alternative location
      default: "Complex Node"             # Safe fallback
    children:
      path: "content.sections.items"      # Navigate to children
      fallback: "body"                    # Alternative structure
```

### 4. Mixed Collections Requiring Normalization

**Problem**: Arrays containing different object types that need uniform handling.

**Solution**: Collection mapping with type normalization:

```yaml
type_overrides:
  MixedContainer:
    children:
      path: "items"
      map:
        template:
          type: "NormalizedItem"          # Consistent type
          original_type: "${item.kind}"   # Preserve original
          data: "${item}"                 # Full original data
        variable: "item"
  
  NormalizedItem:
    type:                                 # Extract real type
      path: "original_type"
      default: "GenericItem"
    label:
      path: "data.title"
      fallback: "data.name"
      default: "Item"
```

### 5. Format Evolution and Version Support

**Problem**: AST formats change over time or have multiple versions.

**Solution**: Version-aware field mapping:

```yaml
# Support multiple format versions gracefully
type:
  path: "node_type"         # v2 format
  fallback: "type"          # v1 format
  default: "LegacyNode"     # Pre-v1 format

type_overrides:
  Document:
    children:
      path: "content"       # v2 format
      fallback: "body"      # v1 format
      default: []           # No children in legacy
    label:
      path: "metadata.title"     # v2 location
      fallback: "title"          # v1 location
      default: "Document"        # No title available
```

### 6. Native AST Processing Without Preprocessing

**Problem**: Need to handle raw AST format without data transformation.

**Solution**: Complete declarative transformation:

```yaml
# Handle Pandoc's native format without preprocessing
type:
  path: "t"
  default: "Unknown"              # Root has no 't' field

type_overrides:
  Unknown:
    type: "Pandoc"                # Transform to meaningful type
    children: "blocks"            # Root children in 'blocks'
    label: "Pandoc Document"      # Static label
  
  Header:
    children:
      path: "c[2]"                # Content in third array element
    label:
      path: "c[2]"                # Same content for label
      transform:
        - name: "filter"          # Keep only String nodes
          t: "Str"
        - name: "extract"         # Extract text content
          field: "c"
        - name: "join"            # Combine words
          separator: " "
        - name: "prefix"          # Add indicator
          prefix: "H"
      default: "Header"
```

### 7. Collection Synthesis for Structural Gaps

**Problem**: Source has raw arrays that need to become structured nodes.

**Solution**: Multi-stage collection mapping:

```yaml
type_overrides:
  List:
    children:
      path: "items"               # Raw array of list items
      map:
        template:
          t: "ListItem"           # Create synthetic type
          content: "${item}"      # Wrap original content
        variable: "item"
  
  ListItem:                       # Process synthetic nodes
    label:
      path: "content[0].text"     # Navigate wrapped structure
      transform:
        - name: "filter"
          type: "text"
        - name: "extract"
          field: "value"
        - name: "join"
          separator: " "
        - name: "truncate"
          max_length: 40
          suffix: "..."
      default: "List Item"
```

### 8. Multi-Level Error Resilience

**Problem**: Complex formats with many potential failure points.

**Solution**: Comprehensive fallback strategy:

```yaml
# Error handling at every level
type:
  path: "nodeType"
  fallback: "type"
  default: "Unknown"

type_overrides:
  ComplexNode:
    label:
      path: "title"               # Primary source
      fallback: "name"            # First fallback
      transform:                  # Process if found
        - name: "strip"
        - name: "truncate"
          max_length: 50
      default: "Unnamed"          # Final fallback
    
    children:
      path: "content"             # Primary children
      fallback: "body"            # Alternative location
      transform:                  # Clean if found
        - name: "filter"
          valid: true
      default: []                 # Empty if nothing works
    
    icon:
      path: "meta.icon"           # Custom icon
      default: "📄"               # Fallback icon
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

## Adapter Definition Formats

The 3viz system supports declarative adapter definitions in two formats that can be used with both the CLI and library, plus a programmatic Python API format for library-only usage.

### Declarative Formats (CLI and Library)

Both declarative formats are fully supported, with YAML recommended due to its support for comments:

#### YAML Format (Recommended)

```yaml
# YAML supports comments for better documentation
type: "t"
children: "c"
icons:
  Header: "H"
  Para: "¶"
type_overrides:
  Header:
    # Complex processing with inline documentation
    label:
      path: "c[2]"
      transform:
        - name: "filter"      # Keep only text nodes
          t: "Str"
        - name: "join"        # Combine into string
          separator: " "
```

#### JSON Format

```json
{
  "type": "t",
  "children": "c",
  "icons": {
    "Header": "H",
    "Para": "¶"
  }
}
```

### Python API Format (Library Only)

For programmatic adapter definition using the Python library:

```python
from treeviz.adapters.extraction.engine import AdapterDef

# Define adapter programmatically
adapter = AdapterDef(
    type="t",
    children="c",
    icons={"Header": "H", "Para": "¶"},
    type_overrides={
        "Header": {
            "label": {
                "path": "c[2]",
                "transform": [
                    {"name": "filter", "t": "Str"},
                    {"name": "join", "separator": " "}
                ]
            }
        }
    }
)
```

## Best Practices

### Development Approach

1. **Start Simple** - Begin with basic field mappings, add complexity as needed
2. **Use Transform Pipelines** - Prefer declarative transforms over custom functions  
3. **Handle Errors Gracefully** - Always provide fallbacks and defaults at multiple levels
4. **Test with Real Data** - Test with various input structures and edge cases
5. **Document Complex Logic** - Use YAML comments to explain sophisticated patterns

### Handling Challenging Formats

6. **Use Type Defaults** - Leverage `{path: "field", default: "fallback"}` for missing fields
7. **Transform Types When Needed** - Use type overrides to convert `Unknown` to meaningful types
8. **Support Format Evolution** - Use fallback chains for different format versions
9. **Process Native AST** - Avoid data preprocessing; handle raw formats declaratively
10. **Layer Your Fallbacks** - Provide fallbacks at field, transform, and type levels

### Performance and Maintenance

11. **Cache Expensive Operations** - The system caches transform results automatically
12. **Use Collection Mapping** - Prefer collection mapping over preprocessing for structural changes
13. **Test Edge Cases** - Verify behavior with missing fields, empty collections, and malformed data
14. **Version Your Adapters** - Document format compatibility and migration paths

## Examples Repository

See `docs/adapter-walkthrough.md` for a detailed walkthrough of the Pandoc adapter, which demonstrates all these features in practice on a real-world complex AST format.
