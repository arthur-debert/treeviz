# 3viz Output Format

3viz provides multiple output formats to suit different use cases, from human-readable terminal output to machine-processable JSON.

## Output Formats

**term**: Terminal-friendly with icons and colors (default for terminals)
- Uses Unicode icons for visual distinction
- Automatic width detection
- Color coding for different elements
- Best for interactive exploration

**text**: Plain text without special formatting (default for pipes)
- ASCII-safe output
- No Unicode icons or colors
- Suitable for logs, emails, documentation
- Consistent across all environments

**json**: Machine-readable JSON structure
- Complete data preservation
- Easy to parse programmatically
- Includes all metadata and source locations
- Perfect for further processing

**yaml**: Human-readable YAML format
- Structured but readable
- Good for configuration files
- Preserves hierarchical relationships
- Easy to edit manually

## Understanding the Output

Each line represents a node in the tree:

```
⧉ Document                                                     7L
  ⊤ Heading: "Getting Started"                                 1L
    ↵ Getting Started                                           1L
  ¶ Paragraph                                                   2L
    ↵ This is the first line of the paragraph.                 1L
    ↵ This is the second line.                                 1L
```

**Structure**:
- Indentation shows hierarchy
- Icons indicate node types  
- Labels show node content or type
- Line counts (7L, 1L, 2L) show content size
- Extra metadata appears after labels

**Common Icons**:
- ⧉ Document/Root
- ⊤ Heading
- ¶ Paragraph  
- ↵ Text/Line
- ☰ List
- • List Item
- 𝒱 Code Block
- ƒ Inline Code