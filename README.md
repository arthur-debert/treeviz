# 3viz, a terminal ast vizualizer for document based ASTs

3viz is designed to simplify reasing about document tree. The 1-line per node and colunar layout makes
scanning and grokking structure easy, while the texttual represntations, icons and extra give
additional informattion at a glance.

Being line based, it makes diffing trees useful and can be invaluable in debugging these parse trees.

This is a sample output:

```text

⧉ Document                                                                                                                                         7L
  ¶ This is a paragraph:                                                                                                                         2L
    ↵ This is a paragraph:                                                                                                                       1L
    ↵ With two lines.                                                                                                                               1L
    ↵ This documenent is the nanos spec, showing all elemetns, but not covering their full variation   1L
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

threeviz is available in pypi as threeviz-py, and can be installed however you get your python packages:

 ```bash
$ pipx install threeviz-py # recommended as it's available globally
  ```

## Using 3viz

3viz can be used as a cli:

 ```bash
  $ 3viz <tree path> <tree-format>
  ```

Or as a library.

  ```python
  from threeviz import threeviz

# both document and format can be a path to a file, the strings or a python object

  threeviz.render (document, format)
  ```

 TODO: add a threw liner example of generating an adapter definition with python for a simple remapping

### Included adapters

  (list each with name and descripton)

### Learn more

Read the docs/user-guide.md for a more complete introduction, learn about the the visual output docs/theui.md or a in-depth doc on docs/adapters.md and learn by example with docs/adapter-walkthrough.md
