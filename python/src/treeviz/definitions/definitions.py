"""
Configuration Management for 3viz

This module handles loading and validating definition files for the
declarative converter. Supports JSON definition files with validation
and helpful error messages.

## Configuration Format

3viz uses JSON definition files to define how AST nodes are converted and displayed.
A definition file contains four main sections:

### Configuration Sections

#### 1. attributes (required)
Maps 3viz node properties to source node attributes:
- `label`: Property containing the text to display
- `type`: Property containing the node type  
- `children`: Property containing child nodes

#### 2. icons (optional)
Maps node types to display symbols using Unicode characters

#### 3. type_overrides (optional)
Overrides attributes for specific node types, allowing per-type customization

#### 4. ignore_types (optional)
List of node types to skip during conversion

### Configuration Files

See the actual definition files for examples:
- `treeviz/definitions/mdast.json` - Markdown AST format
- `treeviz/definitions/unist.json` - Universal Syntax Tree format

### Advanced Configuration

For complex attribute extraction, you can specify nested paths like:
- `"label": "props.title"` - Access nested properties
- `"type": "node.type"` - Deep object access
- `"children": "content.children"` - Nested arrays

### Built-in Configurations

3viz includes built-in definitions for popular formats loaded from files.
Use them with:
```python
from treeviz.definitions import get_builtin_def
def_ = get_builtin_def("mdast")
```

### Configuration Loading

Configurations are loaded and merged with defaults:
1. Default definition provides base settings
2. User definition overrides specific values  
3. Result includes all necessary fields

```python
from treeviz.definitions import load_def

# Load from file
def_ = load_def(def_path="my_def.json")

# Load from dictionary
def_ = load_def(def_dict={"icons": {"custom": "★"}})

# Use defaults only
def_ = load_def()
```
"""




# Deep merge functionality moved to Definition.merge_with() method
