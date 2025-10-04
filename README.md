# 3viz, a terminal AST visualizer for document trees

3viz is designed to simplify reasoning about document trees. The one-line-per-node and columnar layout makes scanning and understanding structure easy, while the textual representations, icons and metadata provide additional information at a glance.

Being line-based, it makes diffing trees useful and can be invaluable in debugging parse trees.

This is a sample output:

```text

⧉ Document                                                                                                                                         7L
  ¶ This is a paragraph:                                                                                                                         2L
    ↵ This is a paragraph:                                                                                                                       1L
    ↵ With two lines.                                                                                                                               1L
    ↵ This document is the nanos spec, showing all elements, but not covering their full variation   1L
  № List                                                                                                                            type=ordered 2L
    §"Session And titles                                                                                                                           2L
      ⊤"Session And titles                                                                                                                        1L
      ⊡ Content                                                                                                                                         1L
        № List                                                                                                                     type=ordered  1L
          •     2. Core Elements                                                                                                                  2L
            ◦     2. Core Elements                                                                                                               1L
            ⊡ Content                                                                                                                                  1L
              ¶         Which should have at least one item.                                                                          1L
                ↵ Which should have at least one item.                                                                                1L
  𝒱 4. A simple code block: (-)                                                                                              13L
  ```

## Installing

3viz is available on PyPI as treeviz-py, and can be installed with your preferred Python package manager:

```bash
$ pipx install treeviz-py  # recommended for global availability
```

## Using 3viz

3viz can be used as a CLI:

```bash
$ 3viz <tree_path> <tree_format>
```

Or as a library:

```python
from treeviz import generate_viz

# Both document and format can be a path to a file, strings, or Python objects
generate_viz(document, format)
```

### Built-in adapters

- **mdast**: Markdown Abstract Syntax Tree format used by remark and other Markdown processors
- **unist**: Universal Syntax Tree format, the base format for unified ecosystem parsers
- **pandoc**: Pandoc's JSON AST format for converting between markup formats
- **restructuredtext**: reStructuredText document trees from the docutils library

### Learn more

- [User Guide](docs/user-guide.md) - Complete introduction to using 3viz
- [Visual Output Guide](docs/theui.md) - Understanding the visualization format
- [Adapters Documentation](docs/adapters.md) - In-depth guide to creating custom adapters
- [Adapter Walkthrough](docs/adapter-walkthrough.md) - Step-by-step examples
