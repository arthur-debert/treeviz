This directory contains MediaWiki test files (.mw) and their corresponding Abstract Syntax Tree (AST) representations in JSON format (.json). The ASTs are generated using the `mwparserfromhell` Python library.

## AST Structure

The JSON AST has a hierarchical structure, with the root object always being of type `Wikicode`.

### Root Object
- `type`: "Wikicode"
- `nodes`: An array of node objects that represent the content of the parsed document.

### Node Objects
Each object within the `nodes` array represents a part of the document and has a `type` field indicating its nature. All textual content is recursively parsed and contained within nested `Wikicode` objects.

### Common Node Types

- **`Text`**: Represents plain text content.
  - `value`: (string) The text content.

- **`Heading`**: Represents a section heading (e.g., `= Heading =`).
  - `level`: (integer) The heading level (1-6).
  - `title`: (Wikicode) The content of the heading.

- **`Wikilink`**: Represents an internal link (e.g., `[[Page Title|Link Text]]`).
  - `title`: (Wikicode) The target page title.
  - `text`: (Wikicode) The display text for the link (if provided).

- **`ExternalLink`**: Represents an external link (e.g., `[https://example.com Link Text]`).
  - `url`: (Wikicode) The URL of the link.
  - `title`: (Wikicode) The display text for the link.

- **`Template`**: Represents a template transclusion (e.g., `{{TemplateName|param1=value1}}`).
  - `name`: (Wikicode) The name of the template.
  - `params`: (array) A list of `Parameter` objects.

- **`Parameter`**: Represents a parameter within a `Template`.
  - `name`: (Wikicode) The parameter's name.
  - `value`: (Wikicode) The parameter's value.

- **`Tag`**: Represents an HTML tag. This is used for both explicit HTML (e.g., `<pre>`) and for wiki markup that is converted to tags, such as:
  - `''italic''` -> `<i>`
  - `'''bold'''` -> `<b>`
  - `* item` -> `<li>` (Note: The parser generates a `<li>` tag but the list container `<ul>` or `<ol>` is implicit).
  - `----` -> `<hr>`
  - `<s>strike</s>` -> `<s>`
  - `<u>underline</u>` -> `<u>`

  The `Tag` object has the following properties:
  - `tag`: (Wikicode) The name of the tag (e.g., "b", "li").
  - `contents`: (Wikicode) The content inside the tag.
  - `attributes`: (array) A list of attribute objects, each with a `name` and `value`.

- **`Table`**: Represents a wiki table (`{| ... |}`).
  - `attributes`: (array) Attributes applied to the table.
  - `caption`: (Wikicode) The table's caption.
  - `rows`: (array) A list of `TableRow` objects.

This structure provides a detailed and traversable representation of a MediaWiki document, suitable for adaptation and analysis.