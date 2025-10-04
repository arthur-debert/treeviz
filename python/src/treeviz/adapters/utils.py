"""
Utility functions for the adapter system.
"""

import sys
from typing import Callable


def exit_on_error(func: Callable) -> Callable:
    """
    Decorator to exit with status 1 on any exception.

    This implements the "fail fast" principle - any error
    should immediately exit the program with a clear error message.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
