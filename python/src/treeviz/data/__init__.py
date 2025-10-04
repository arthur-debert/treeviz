"""
This package contains built-in adapter definitions for treeviz.

Adapters are registered in the BUILTIN_ADAPTERS dictionary.
The key is the name of the adapter, and the value is the
adapter definition dictionary.
"""

from .restructuredtext import definition as rst_def

BUILTIN_ADAPTERS = {
    "restructuredtext": rst_def,
}