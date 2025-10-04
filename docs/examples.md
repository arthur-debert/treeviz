# Adapter Examples

This guide provides practical examples of adapter definitions for common transformation needs, bridging the gap between simple field mapping and complex custom logic.

## Basic Field Mapping

For ASTs that use different field names:

```yaml
# simple-mapping.yaml
type: "node_type"
label: "text_content"
children: "child_nodes"

icons:
  heading: "H"
  paragraph: "¶"
  list: "•"
```

## Content Extraction with Transforms

Extract and format content from nested structures:

```yaml
# content-extraction.yaml
type: "kind"
label:
  extractor: "attribute"
  name: "data.text"
  transform: "lambda t: t[:50] + '...' if len(t) > 50 else t"
children: "children"

type_overrides:
  header:
    label:
      extractor: "attribute" 
      name: "data.level"
      transform: "lambda level: f'H{level}'"
  
  code_block:
    label:
      extractor: "attribute"
      name: "data.language"
      transform: "lambda lang: f'Code ({lang})'"
    children: []

icons:
  header: "⊤"
  paragraph: "¶"
  code_block: "```"
  list_item: "›"
```

## Conditional Logic

Handle nodes that may or may not have certain fields:

```yaml
# conditional-logic.yaml
type: "type"
label:
  extractor: "method"
  name: "get_display_text"
children: "children"

type_overrides:
  section:
    label:
      extractor: "attribute"
      name: "title"
      transform: "lambda t: t if t else 'Untitled Section'"
  
  link:
    label:
      extractor: "attribute"
      name: "href"
      transform: "lambda url: f'Link: {url[:30]}...' if len(url) > 30 else f'Link: {url}'"
    children: []

  image:
    label:
      extractor: "attribute"
      name: "alt"
      transform: "lambda alt: f'Image: {alt}' if alt else 'Image'"
    children: []

ignore_types:
  - "whitespace"
  - "comment"

icons:
  section: "§"
  paragraph: "¶"
  link: "🔗"
  image: "🖼"
  emphasis: "𝑖"
  strong: "𝐁"
```

## List and Container Handling

Special handling for container elements:

```yaml
# container-handling.yaml
type: "tagName"
label: "tagName"
children: "children"

type_overrides:
  ul:
    label: "Unordered List"
    
  ol:
    label:
      extractor: "attribute"
      name: "start"
      transform: "lambda start: f'Ordered List (start: {start})' if start else 'Ordered List'"
  
  li:
    label:
      extractor: "method"
      name: "get_text_preview"
      transform: "lambda text: text[:40] + '...' if len(text) > 40 else text"
  
  table:
    label:
      extractor: "attribute"
      name: "children"
      transform: "lambda rows: f'Table ({len(rows)} rows)'"
  
  blockquote:
    label: "Quote"

icons:
  ul: "•"
  ol: "№"
  li: "›"
  table: "▦"
  blockquote: "❝"
  p: "¶"
  h1: "⊤"
  h2: "⊤"
  h3: "⊤"
```

## Working with Metadata

Extract and display node metadata:

```yaml
# metadata-display.yaml
type: "type"
label: "text"
children: "children"

type_overrides:
  element:
    label:
      extractor: "attribute"
      name: "tagName"
    extra:
      class:
        extractor: "attribute"
        name: "properties.className"
        transform: "lambda classes: ' '.join(classes) if classes else None"
      id:
        extractor: "attribute"
        name: "properties.id"
  
  code:
    label:
      extractor: "attribute"
      name: "value"
      transform: "lambda code: f'Code: {code[:20]}...' if len(code) > 20 else f'Code: {code}'"
    extra:
      language:
        extractor: "attribute"
        name: "lang"
    children: []

icons:
  element: "◦"
  text: "T"
  code: "`"
  root: "⧉"
```

## Complex Node Transformation

Handle irregular tree structures:

```yaml
# complex-transformation.yaml
type: "nodeType"
label: "title"
children: "body"

type_overrides:
  document:
    label: "Document"
    children: "sections"
  
  section:
    children:
      extractor: "method"
      name: "get_content_nodes"
    
  definition_list:
    children:
      extractor: "attribute"
      name: "items"
      transform: "lambda items: [{'nodeType': 'definition_item', 'term': item['term'], 'definition': item['def']} for item in items]"
  
  definition_item:
    label:
      extractor: "attribute"
      name: "term"
    children:
      extractor: "attribute"
      name: "definition"

ignore_types:
  - "metadata"
  - "system_message"

icons:
  document: "📄"
  section: "§"
  paragraph: "¶"
  definition_list: "📝"
  definition_item: "›"
```

These examples demonstrate progressively more complex adapter configurations, showing how to handle real-world AST transformation challenges while maintaining clean, readable definitions.