"""
Advanced Extraction Engine for 3viz

This package provides enhanced declarative extraction capabilities including:
- Complex path expressions with dot notation and array access
- Conditional extraction with fallback chains and default values  
- Transformation functions for data manipulation
- Advanced filtering with complex predicates
"""

from .engine import extract_attribute
from .path_evaluator import extract_by_path
from .path_parser import parse_path_expression
from .transforms import apply_transformation
from .filters import filter_collection

__all__ = [
    "extract_attribute",
    "extract_by_path",
    "parse_path_expression",
    "apply_transformation",
    "filter_collection",
]
