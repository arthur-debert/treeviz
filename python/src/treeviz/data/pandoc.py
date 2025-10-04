"""
Adapter for Pandoc's JSON AST format.

This adapter includes a workaround for an inconsistency in the Pandoc AST
and a proposal for a future feature to make such hacks unnecessary.

## Implementation Notes & Hack

The standard Pandoc AST has an inconsistency: the root object does not have a
`t` (type) key, while all content nodes do. To work around this, this adapter
relies on the data being pre-processed to add a `t` key to the root,
making the tree uniformly structured. The test file for this adapter
demonstrates how to do this on the fly.
"""

definition = {
    # Default extractors
    "type": "t",
    "children": "c",
    "label": "t",

    # Type-specific overrides
    "type_overrides": {
        "Pandoc": {
            "children": "blocks",
            # Use a lambda to return a literal string, avoiding path parsing.
            "label": lambda n: "Pandoc Document"
        },
        "Header": {
            "children": lambda n: n['c'][2],
            "label": lambda n: 'H' + str(n['c'][0]) + ': ' + (''.join(x.get('c', ' ') if x.get('t') == 'Str' else ' ' for x in n['c'][2])).strip()
        },
        "Para": {
            "label": lambda n: ((''.join(x.get('c', ' ') if x.get('t') == 'Str' else ' ' for x in n.get('c', []))).strip()[:60] + '...') if n.get('c') else 'Paragraph'
        },
        "CodeBlock": {
            "children": [],
            "label": lambda n: 'CodeBlock(' + (n['c'][0][1][0] if n['c'][0][1] else 'text') + ')'
        },
        "BulletList": {
            "children": lambda n: [{'t': 'ListItem', 'c': item} for item in n['c']],
            "label": lambda n: "Bullet List"
        },
        "OrderedList": {
            "children": lambda n: [{'t': 'ListItem', 'c': item} for item in n['c'][1]],
            "label": lambda n: "Ordered List"
        },
        "BlockQuote": {
            "label": lambda n: "BlockQuote"
        },
        "Table": {
            "children": [],
            "label": lambda n: "Table"
        },
        "ListItem": {
            "label": lambda n: ((''.join(x.get('c', ' ') if x.get('t') == 'Str' else ' ' for x in n['c'][0].get('c', []))).strip()[:60] + '...') if n.get('c') and n['c'][0].get('c') else 'List Item'
        },
        "Plain": {
            "label": lambda n: ((''.join(x.get('c', ' ') if x.get('t') == 'Str' else ' ' for x in n.get('c', []))).strip()[:60] + '...') if n.get('c') else 'Plain'
        },
        "Str": {
            "children": [],
            "label": "c"
        },
        "Code": {
            "children": [],
            "label": lambda n: n['c'][1]
        },
        "Emph": {
            "label": lambda n: "Emph"
        },
        "Strong": {
            "label": lambda n: "Strong"
        },
        "Link": {
            "label": lambda n: n['c'][2][0]
        }
    },

    "ignore_types": [
        "Space",
        "SoftBreak",
        "LineBreak"
    ],

    "icons": {
        "Pandoc": "📄", "Header": "H", "Para": "¶", "CodeBlock": "```",
        "BulletList": "•", "OrderedList": "1.", "ListItem": "›",
        "BlockQuote": ">", "Table": "▦", "Str": "T", "Code": "`",
        "Emph": "𝑖", "Strong": "💪", "Link": "🔗", "Plain": "p"
    }
}