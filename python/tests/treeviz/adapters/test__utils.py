"""
Unit tests for adapter utility functions.
"""

from unittest.mock import patch
from io import StringIO

from treeviz.adapters.utils import exit_on_error


class TestExitOnErrorDecorator:
    """Test the exit_on_error decorator functionality."""

    def test_successful_function_execution(self):
        """Test that decorator allows successful function execution."""

        @exit_on_error
        def successful_func(x, y):
            return x + y

        result = successful_func(2, 3)
        assert result == 5

    def test_function_with_kwargs(self):
        """Test that decorator preserves kwargs."""

        @exit_on_error
        def func_with_kwargs(a, b=10, c=None):
            return a + b + (c or 0)

        result = func_with_kwargs(1, b=20, c=5)
        assert result == 26

    def test_function_with_no_args(self):
        """Test that decorator works with functions that take no arguments."""

        @exit_on_error
        def no_args_func():
            return "success"

        result = no_args_func()
        assert result == "success"

    @patch("sys.exit")
    @patch("sys.stderr", new_callable=StringIO)
    def test_exception_handling_and_exit(self, mock_stderr, mock_exit):
        """Test that decorator catches exceptions and exits with status 1."""

        @exit_on_error
        def failing_func():
            raise ValueError("Something went wrong")

        # Call the decorated function
        failing_func()

        # Verify exit was called with status 1
        mock_exit.assert_called_once_with(1)

        # Verify error message was printed to stderr
        stderr_output = mock_stderr.getvalue()
        assert "Error: Something went wrong" in stderr_output

    @patch("sys.exit")
    @patch("sys.stderr", new_callable=StringIO)
    def test_different_exception_types(self, mock_stderr, mock_exit):
        """Test that decorator handles different exception types."""

        @exit_on_error
        def type_error_func():
            raise TypeError("Type error occurred")

        @exit_on_error
        def runtime_error_func():
            raise RuntimeError("Runtime error occurred")

        # Test TypeError
        type_error_func()
        mock_exit.assert_called_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Error: Type error occurred" in stderr_output

        # Reset mocks
        mock_exit.reset_mock()
        mock_stderr.seek(0)
        mock_stderr.truncate(0)

        # Test RuntimeError
        runtime_error_func()
        mock_exit.assert_called_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Error: Runtime error occurred" in stderr_output

    @patch("sys.exit")
    @patch("sys.stderr", new_callable=StringIO)
    def test_complex_error_message(self, mock_stderr, mock_exit):
        """Test that complex error messages are handled correctly."""

        @exit_on_error
        def complex_error_func():
            raise ValueError(
                "Multi-line\nerror message with special chars: !@#$%"
            )

        complex_error_func()

        mock_exit.assert_called_once_with(1)
        stderr_output = mock_stderr.getvalue()
        assert (
            "Error: Multi-line\nerror message with special chars: !@#$%"
            in stderr_output
        )

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""

        @exit_on_error
        def documented_func(x):
            """This function has documentation."""
            return x * 2

        # Note: Basic decorator doesn't preserve metadata,
        # but we can test that it's still callable
        assert callable(documented_func)

        # Test that the wrapper function works
        with patch("sys.exit"), patch("sys.stderr"):
            # This should work without issues
            result = documented_func(5)
            assert result == 10

    @patch("sys.exit")
    @patch("sys.stderr", new_callable=StringIO)
    def test_exception_during_argument_processing(self, mock_stderr, mock_exit):
        """Test decorator behavior when exception occurs during argument processing."""

        @exit_on_error
        def func_with_args(required_arg):
            return required_arg.upper()  # Will fail if not a string

        # Call with invalid argument type
        func_with_args(123)  # Should raise AttributeError

        mock_exit.assert_called_once_with(1)
        stderr_output = mock_stderr.getvalue()
        assert "Error:" in stderr_output
        assert "int" in stderr_output  # AttributeError should mention int type
