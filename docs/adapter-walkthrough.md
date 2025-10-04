# Pandoc Adapter Walkthrough

This document provides an in-depth walkthrough of the Pandoc adapter, demonstrating how 3viz's declarative adapter system transforms complex AST structures without custom code. The Pandoc adapter showcases every feature of the system working together to handle one of the most complex document AST formats.

## Understanding Pandoc AST Format

Pandoc represents documents as JSON Abstract Syntax Trees with a specific structure. Understanding this format is crucial to appreciating how the adapter works.

### Basic Pandoc Structure

```json
{
  "pandoc-api-version": [1, 23, 1],
  "meta": {},
  "blocks": [
    {
      "t": "Header",
      "c": [1, ["id", [], []], [{"t": "Str", "c": "Title"}]]
    },
    {
      "t": "Para", 
      "c": [{"t": "Str", "c": "Content"}]
    }
  ]
}
```

### Key Patterns in Pandoc AST

1. **Node Structure**: Every node has `t` (type) and `c` (content) fields
2. **Nested Arrays**: Content often contains arrays of arrays for complex structures
3. **Inline Elements**: Text is broken into multiple `Str` and `Space` nodes
4. **Attribute Lists**: Elements often have `[id, classes, attributes]` tuples

## Adapter Definition Overview

The Pandoc adapter (`pandoc.yaml`) demonstrates the full power of the declarative system:

```yaml
# Default extraction patterns for all node types
type: "t"                # Pandoc nodes have their type in the 't' field
children: "c"           # Child content is typically in the 'c' field  
label: "t"              # Default label is just the node type

# Type-specific overrides for complex processing
type_overrides: {...}

# Visual icons for immediate recognition
icons: {...}

# Node types to skip during traversal
ignore_types: [...]
```

## Root Document Processing

### Problem: Inconsistent Root Structure

Pandoc's root document doesn't follow the standard `{t, c}` pattern:

```json
{
  "pandoc-api-version": [...],
  "meta": {...},
  "blocks": [...]  // ← Children are here, not in 'c'
}
```

### Solution: Custom Root Handling

```yaml
type_overrides:
  Pandoc:
    children: "blocks"        # Override default 'c' field
    label: "Pandoc Document" # Static label instead of type
```

**Key Features Demonstrated:**

- Static label assignment
- Custom children field mapping
- Type override system

## Header Processing

### Problem: Complex Nested Structure

Headers have a complex nested structure with level, attributes, and content:

```json
{
  "t": "Header",
  "c": [
    1,                           // Level
    ["id", [], []],             // Attributes
    [                           // Content (array of inline elements)
      {"t": "Str", "c": "This"},
      {"t": "Space"},
      {"t": "Str", "c": "is"},
      {"t": "Space"},
      {"t": "Str", "c": "title"}
    ]
  ]
}
```

### Solution: Transform Pipeline

```yaml
Header:
  children: 
    path: "c[2]"              # Extract content from third element
  label:
    path: "c[2]"              # Same content for label processing
    transform:
      - name: "filter"        # 1. Filter to only String nodes
        t: "Str"
      - name: "extract"       # 2. Extract 'c' field from each
        field: "c"
      - name: "join"          # 3. Join into single string
        separator: " "
      - name: "prefix"        # 4. Add header indicator
        prefix: "H"
    default: "Header"         # Fallback if processing fails
```

**Key Features Demonstrated:**

- Array indexing with `c[2]`
- Multi-step transform pipeline
- Collection filtering and extraction
- String processing and formatting
- Graceful error handling with defaults

**Pipeline Flow:**

1. Input: `[{"t": "Str", "c": "This"}, {"t": "Space"}, {"t": "Str", "c": "is"}, ...]`
2. Filter: `[{"t": "Str", "c": "This"}, {"t": "Str", "c": "is"}, ...]`
3. Extract: `["This", "is", "title"]`
4. Join: `"This is title"`
5. Prefix: `"HThis is title"`

## Paragraph Processing

### Problem: Mixed Inline Content

Paragraphs contain mixed inline elements including text, spaces, formatting:

```json
{
  "t": "Para",
  "c": [
    {"t": "Str", "c": "This"},
    {"t": "Space"},
    {"t": "Strong", "c": [{"t": "Str", "c": "bold"}]},
    {"t": "Space"},
    {"t": "Str", "c": "text"}
  ]
}
```

### Solution: Recursive Text Extraction

```yaml
Para:
  label:
    path: "c"
    transform:
      - name: "filter"        # Keep only text nodes
        t: "Str"
      - name: "extract"       # Extract text content
        field: "c"
      - name: "join"          # Combine into readable text
        separator: " "
      - name: "truncate"      # Prevent overly long labels
        max_length: 60
        suffix: "..."
    default: "Paragraph"
```

**Key Features Demonstrated:**

- Collection filtering by type
- Text extraction and cleanup
- Length management with truncation
- Readable label generation

## Code Block Processing

### Problem: Deeply Nested Language Information

Code blocks store language information in a deeply nested structure:

```json
{
  "t": "CodeBlock",
  "c": [
    [                         // Attributes
      "",                     // ID
      ["python"],            // Classes (language is here!)
      []                      // Key-value attributes
    ],
    "print('Hello World')"    // Code content
  ]
}
```

### Solution: Deep Path Access

```yaml
CodeBlock:
  children: []              # Leaf node - no children
  label:
    path: "c[0][1][0]"      # Navigate to language: c[0][1][0]
    transform:
      - name: "prefix"
        prefix: "CodeBlock("
      - name: "str"           # Ensure string type
      - name: "prefix"        # Close parenthesis (note: this is incorrect!)
        prefix: ")"
    default: "CodeBlock(text)"
```

**Key Features Demonstrated:**

- Deep nested path access
- Multiple path components
- String formatting
- Default fallback for missing languages

**Path Breakdown:**

- `c` → `[attributes, code]`
- `[0]` → `attributes`
- `[1]` → `["python"]` (classes array)
- `[0]` → `"python"` (first class)

## List Processing with Collection Mapping

### Problem: Raw Arrays Need Structure

Lists contain raw arrays that need to be transformed into proper nodes:

```json
{
  "t": "BulletList",
  "c": [
    [{"t": "Plain", "c": [{"t": "Str", "c": "Item 1"}]}],
    [{"t": "Plain", "c": [{"t": "Str", "c": "Item 2"}]}]
  ]
}
```

### Solution: Collection Mapping

```yaml
BulletList:
  children:
    path: "c"                 # Raw array of list items
    map:
      template:               # Template for synthetic nodes
        t: "ListItem"         # Create ListItem type
        c: "${item}"          # Wrap original content
      variable: "item"        # Variable name for each item
  label: "Bullet List"       # Static label

# Process the synthetic ListItem nodes
ListItem:
  label:
    path: "c[0].c"           # Navigate to first child's content
    transform:
      - name: "filter"
        t: "Str"
      - name: "extract"
        field: "c"
      - name: "join"
        separator: " "
      - name: "truncate"
        max_length: 60
        suffix: "..."
    default: "List Item"
```

**Key Features Demonstrated:**

- Collection mapping with templates
- Synthetic node creation
- Template variable substitution
- Two-stage processing (map then process)

**Collection Mapping Flow:**

1. Input: `[[{"t": "Plain", "c": [...]}], [{"t": "Plain", "c": [...]}]]`
2. Map: `[{"t": "ListItem", "c": [...]}, {"t": "ListItem", "c": [...]}]`
3. Process: Each ListItem is then processed by its own rules

## Ordered List Variation

### Problem: Different Structure

Ordered lists have a different structure with metadata:

```json
{
  "t": "OrderedList",
  "c": [
    [1, {"t": "Decimal"}, {"t": "Period"}],  // List attributes
    [                                         // List items (different position!)
      [{"t": "Plain", "c": [...]}],
      [{"t": "Plain", "c": [...]}]
    ]
  ]
}
```

### Solution: Different Path

```yaml
OrderedList:
  children:
    path: "c[1]"             # Items are in second element, not first
    map:
      template:
        t: "ListItem"
        c: "${item}"
      variable: "item"
  label: "Ordered List"
```

**Key Features Demonstrated:**

- Handling format variations
- Path adaptation for different structures
- Consistent output despite input differences

## String and Inline Processing

### Simple Content Extraction

```yaml
# String nodes - direct content access
Str:
  children: []              # Leaf nodes have no children
  label: "c"               # Direct field access

# Inline code - nested content
Code:
  children: []
  label:
    path: "c[1]"           # Code content is in second element
    default: "code"
```

### Formatting Nodes

```yaml
# Static labels for formatting
Emph:
  label: "Emph"            # Emphasis formatting

Strong:
  label: "Strong"          # Strong formatting
```

**Key Features Demonstrated:**

- Simple field access patterns
- Static label assignment
- Leaf node handling

## Link Processing

### Problem: Deeply Nested URLs

Links have complex nested structure with URL buried deep:

```json
{
  "t": "Link",
  "c": [
    [{"t": "Str", "c": "text"}],           // Link text
    [                                      // Link target
      "http://example.com",               // URL (here!)
      "title"
    ]
  ]
}
```

### Solution: Deep Path Access

```yaml
Link:
  label:
    path: "c[2][0]"         # Navigate to URL: c[2][0]
    default: "Link"
```

**Key Features Demonstrated:**

- Deep nested access for metadata
- Extracting meaningful information for labels
- Fallback for malformed links

## Visual Enhancement with Icons

### Comprehensive Icon Mapping

```yaml
icons:
  Pandoc: "📄"             # Document
  Header: "H"              # Header levels
  Para: "¶"                # Paragraph symbol
  CodeBlock: "```"         # Code block indicator
  BulletList: "•"          # Bullet point
  OrderedList: "1."        # Numbered list
  ListItem: "›"            # List item arrow
  BlockQuote: ">"          # Quote indicator
  Table: "▦"               # Table grid
  Str: "T"                 # Text
  Code: "`"                # Inline code
  Emph: "𝑖"                # Italic indicator
  Strong: "💪"             # Bold indicator  
  Link: "🔗"               # Link symbol
  Plain: "p"               # Plain text
```

**Key Features Demonstrated:**

- Type-based icon mapping
- Unicode symbols for visual clarity
- Comprehensive coverage of node types

## Noise Reduction

### Ignoring Irrelevant Nodes

```yaml
ignore_types:
  - "Space"               # Whitespace between words
  - "SoftBreak"           # Soft line breaks
  - "LineBreak"           # Hard line breaks
```

**Key Features Demonstrated:**

- Noise reduction for cleaner visualization
- Focus on structural elements
- Improved readability

## Advanced Patterns Demonstrated

### 1. Multi-Stage Processing

The adapter demonstrates sophisticated multi-stage processing:

1. **Collection Mapping** - Transform raw arrays into structured nodes
2. **Type Override Processing** - Apply type-specific rules to synthetic nodes
3. **Transform Pipelines** - Multi-step data processing
4. **Fallback Handling** - Graceful degradation

### 2. Path Expression Mastery

Complex path expressions navigate Pandoc's nested structure:

- `c[2]` - Array indexing
- `c[0][1][0]` - Deep nested access
- `c[0].c` - Mixed object and array access

### 3. Transform Pipeline Sophistication

Demonstrates every type of transform:

- **Filtering** - `filter` by type
- **Extraction** - `extract` fields from collections
- **Text Processing** - `join`, `truncate`, `prefix`
- **Type Conversion** - `str` for type safety

### 4. Error Resilience

Comprehensive error handling:

- **Default Values** - Every complex extraction has fallbacks
- **Graceful Degradation** - System continues with meaningful defaults
- **Path Validation** - Robust handling of missing fields

## Real-World Usage Example

Given this Pandoc AST input:

```json
{
  "t": "Header",
  "c": [
    2,
    ["introduction", [], []],
    [
      {"t": "Str", "c": "Introduction"},
      {"t": "Space"},
      {"t": "Str", "c": "to"},
      {"t": "Space"},
      {"t": "Str", "c": "3viz"}
    ]
  ]
}
```

The adapter produces this 3viz node:

```
H Introduction to 3viz                               (Icon: H)
  ↵ Introduction                              (Icon: T)
  ↵ to                                        (Icon: T)  
  ↵ 3viz                                      (Icon: T)
```

**Processing Flow:**

1. Node type identified as "Header"
2. Children extracted from `c[2]` → inline elements
3. Label generated through transform pipeline:
   - Filter → `[{"t": "Str", "c": "Introduction"}, {"t": "Str", "c": "to"}, {"t": "Str", "c": "3viz"}]`
   - Extract → `["Introduction", "to", "3viz"]`
   - Join → `"Introduction to 3viz"`
   - Prefix → `"HIntroduction to 3viz"`
4. Icon applied from mapping: "H"
5. Children processed recursively

## Lessons for Other Adapters

The Pandoc adapter teaches valuable patterns for other complex AST formats:

### 1. Handle Format Inconsistencies

Different node types may have different structures. Use type overrides to handle variations while maintaining consistent output.

### 2. Use Transform Pipelines for Complex Processing

Instead of custom functions, chain simple transforms to handle complex data extraction and formatting.

### 3. Leverage Collection Mapping for Structure Synthesis

When the source format has raw arrays that need structure, use collection mapping to create synthetic nodes.

### 4. Provide Comprehensive Fallbacks

Complex formats often have edge cases. Always provide meaningful defaults and fallbacks.

### 5. Focus on Information Architecture

Design your adapter to extract the most meaningful information for visualization while filtering out noise.

## Performance Considerations

The Pandoc adapter demonstrates efficient processing patterns:

1. **Lazy Evaluation** - Children are only processed when accessed
2. **Transform Optimization** - Built-in transforms are optimized for performance
3. **Memory Efficiency** - Templates are lightweight and reusable
4. **Caching** - The system caches transform results where possible

## Extensibility

The declarative approach makes the adapter easily extensible:

1. **New Node Types** - Add new type overrides without touching code
2. **Enhanced Processing** - Modify transform pipelines declaratively
3. **Visual Customization** - Update icons and formatting rules
4. **Format Evolution** - Adapt to new Pandoc versions by updating paths

## Conclusion

The Pandoc adapter showcases how 3viz's declarative adapter system can handle even the most complex AST formats without custom code. Through type overrides, transform pipelines, collection mapping, and comprehensive error handling, it transforms Pandoc's intricate nested JSON structure into clean, readable tree visualizations.

This approach demonstrates that complex document processing can be achieved through configuration rather than programming, making the system accessible to users who understand the source format but may not be comfortable writing transformation code.

The patterns established in this adapter serve as a template for handling other complex formats, providing a roadmap for creating sophisticated AST transformations through declarative configuration.
