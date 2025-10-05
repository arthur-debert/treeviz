#!/usr/bin/env python3
"""Simple example of customizing icons in treeviz"""

from treeviz import render

# Create an adapter with custom icons
my_adapter = {
    "label": "name",
    "type": "type",
    "children": "children",
    "icons": {
        "folder": "📁",
        "python": "🐍",
        "javascript": "🟨",
        "config": "⚙️",
        "test": "🧪",
        "docs": "📚",
    },
}

# Sample data
data = {
    "name": "my-project",
    "type": "folder",
    "children": [
        {"name": "app.py", "type": "python"},
        {"name": "test_app.py", "type": "test"},
        {"name": "config.json", "type": "config"},
        {"name": "README.md", "type": "docs"},
    ],
}

# Render with custom icons
result = render(data, my_adapter)
print(result)
