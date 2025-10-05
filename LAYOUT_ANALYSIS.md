# Treeviz Layout Analysis

Based on the reference outputs, here's how the treeviz layout currently works:

## Layout Components

Each line consists of these components from left to right:

1. **Indentation** (2 spaces per level)
2. **Icon** (Unicode character representing node type)
3. **Space separator**
4. **Label** (node content, responsive width)
5. **Double space separator** (before right-aligned content)
6. **Extras** (optional, from node.extra dict, max 20 chars, right-aligned)
7. **Space separator** (if extras present)
8. **Line count** (right-aligned, format: `NL` where N is number)

## Column Layout Rules

### Fixed Elements

- **Indentation**: 2 spaces × depth level
- **Icon**: 1-2 characters (some Unicode chars display wider)
- **Extras**: Max 20 characters, right-aligned (when present)
- **Line count**: Always right-aligned, typically 2-3 chars + "L"

### Responsive Element

- **Label**: Fills available space between icon and line count
- Truncated with ellipsis (`…`) when too long
- Maintains at least 2 spaces before line count

### Example Layout Analysis

From `3viz_simple_term.txt`:

```
? Project Root                                                                3L
  ? src/                                                                      2L
    ? main.py                                                                 1L
```

Breaking down line 1:

- Indentation: "" (0 spaces, depth 0)
- Icon: "?"
- Separator: " "
- Label: "Project Root" + padding
- Right padding: spaces to align line count
- Line count: "3L" (right-aligned at column 78-79)

From `mdast_comprehensive_term.txt`:

```
  ¶ paragraph                                                                 5L
    ◦ This is a paragraph with                                                1L
    𝐁 strong                                                                  1L
```

Breaking down line 2:

- Indentation: "    " (4 spaces, depth 2)
- Icon: "◦"
- Separator: " "
- Label: "This is a paragraph with" + padding
- Line count: "1L" (right-aligned)

## Width Calculations

For terminal output (`term`):

- Uses actual terminal width (auto-detected)
- In examples: ~80-86 columns

For text output (`text`):

- Fixed at 80 columns

## Special Cases

1. **Long labels**: Truncated with `…` when exceeding available space
   Example: `◦ This is a blockquote with so…`

2. **Multi-byte Unicode icons**: Icons like `𝐁`, `𝐼`, `⧉` may display wider
   but are treated as single characters in calculations

3. **Empty labels**: Some nodes have no label, just icon and line count

## Notes on Extras

The extras functionality is designed but not currently implemented in the legacy renderer:

- Should format `node.extra` dict as `key=value` pairs
- Maximum 20 characters (truncated if longer)
- Would appear between label and line count
- Example: A list node with `extra={"type": "ordered"}` would show `type=ordered`

## Proposed Template-Based Layout

To maintain character-perfect compatibility, our template system should:

1. Use the `calculate_line_layout` function from our layout system
2. Apply Rich styling without affecting character positions
3. Ensure all spacing and alignment matches exactly
4. Format node.extra dict to string for display

The template will wrap content in semantic styles:

```jinja
[icon]{{ icon }}[/icon] [label]{{ label }}[/label]{{ padding }}{% if extras %}[extras]{{ extras }}[/extras] {% endif %}[numlines]{{ count }}L[/numlines]
```

Where:

- `extras` is formatted from node.extra dict (e.g., `{"type": "ordered"}` → `"type=ordered"`)
- `padding` is calculated by layout system to maintain alignment
- Styles only add color/formatting, not spacing
- Layout calculation remains identical to current implementation
