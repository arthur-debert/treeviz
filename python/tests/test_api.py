"""
Test the treeviz public API.

These are mock tests that verify the API calls generate_viz correctly,
since generate_viz itself is already tested.
"""

import pytest
from unittest.mock import patch
from treeviz import render, Adapter, AdapterLib
from treeviz.model import Node


class TestRenderAPI:
    """Test the main render() function."""

    @patch("treeviz.treeviz.generate_viz")
    def test_render_calls_generate_viz_with_file(self, mock_generate_viz):
        """Test that render() calls generate_viz correctly for file inputs."""
        mock_generate_viz.return_value = "mocked output"

        result = render("test.json", "mdast", "json")

        # Verify generate_viz was called with correct arguments
        mock_generate_viz.assert_called_once_with(
            document_path="test.json",
            adapter_spec="mdast",
            output_format="json",
        )
        assert result == "mocked output"

    @patch("treeviz.treeviz.generate_viz")
    def test_render_calls_generate_viz_with_objects(self, mock_generate_viz):
        """Test that render() calls generate_viz correctly for Python objects."""
        mock_generate_viz.return_value = "mocked output"
        test_data = {"type": "root", "children": []}
        custom_adapter = {"label": "name", "type": "type"}

        result = render(test_data, custom_adapter, "text")

        # Verify generate_viz was called with the Python objects
        mock_generate_viz.assert_called_once_with(
            document_path=test_data,
            adapter_spec=custom_adapter,
            output_format="text",
        )
        assert result == "mocked output"

    @patch("treeviz.treeviz.generate_viz")
    def test_render_default_parameters(self, mock_generate_viz):
        """Test render() with default parameters."""
        mock_generate_viz.return_value = "mocked output"
        test_data = {"type": "root"}

        render(test_data)

        # Should use defaults
        mock_generate_viz.assert_called_once_with(
            document_path=test_data, adapter_spec="3viz", output_format="text"
        )

    @patch("treeviz.treeviz.generate_viz")
    def test_render_obj_output_calls_generate_viz_directly(
        self, mock_generate_viz
    ):
        """Test that OBJ output calls generate_viz with obj format directly."""
        # Mock Node object return from generate_viz
        mock_node = Node(label="test", type="root", children=[])
        mock_generate_viz.return_value = mock_node

        test_data = {"type": "root"}
        result = render(test_data, "mdast", "obj")

        # Should call generate_viz with OBJ output directly
        mock_generate_viz.assert_called_once_with(
            document_path=test_data, adapter_spec="mdast", output_format="obj"
        )

        # Should return the Node object from generate_viz
        assert result is mock_node
        assert isinstance(result, Node)

    def test_render_with_adapter_object(self):
        """Test render() with Adapter object."""
        with patch("treeviz.treeviz.generate_viz") as mock_generate_viz:
            mock_generate_viz.return_value = "mocked output"

            adapter_obj = Adapter(label="name", type="type")
            test_data = {"type": "root"}

            render(test_data, adapter_obj, "json")

            # Should pass the adapter object directly
            mock_generate_viz.assert_called_once_with(
                document_path=test_data,
                adapter_spec=adapter_obj,
                output_format="json",
            )

    def test_render_validation_delegated_to_generate_viz(self):
        """Test that output format validation is delegated to generate_viz."""
        with patch("treeviz.treeviz.generate_viz") as mock_generate_viz:
            # Make generate_viz raise an error for invalid output format
            mock_generate_viz.side_effect = ValueError(
                "Unknown output format: invalid"
            )

            test_data = {"type": "root"}

            with pytest.raises(
                ValueError, match="Unknown output format: invalid"
            ):
                render(test_data, "3viz", "invalid")

            # Should have tried to call generate_viz
            mock_generate_viz.assert_called_once()


class TestAdapterLib:
    """Test the AdapterLib class."""

    def test_adapter_lib_list(self):
        """Test AdapterLib.list_formats() returns available adapters."""
        adapters = AdapterLib.list_formats()

        assert isinstance(adapters, list)
        assert "3viz" in adapters
        # Should include built-in adapters from the Lib
        assert any(adapter in ["mdast", "unist"] for adapter in adapters)

    def test_adapter_lib_get_builtin(self):
        """Test AdapterLib.get() with built-in adapters."""
        # Test 3viz (special case)
        adapter = AdapterLib.get("3viz")
        assert isinstance(adapter, Adapter)

        # Test other built-in adapters
        if "mdast" in AdapterLib.list_formats():
            adapter = AdapterLib.get("mdast")
            assert isinstance(adapter, Adapter)

    def test_adapter_lib_get_unknown(self):
        """Test AdapterLib.get() with unknown adapter."""
        with pytest.raises(KeyError):
            AdapterLib.get("nonexistent_adapter")


class TestAPIIntegration:
    """Test that the API components work together."""

    def test_api_workflow_mocked(self):
        """Test complete API workflow with mocks."""
        with patch("treeviz.treeviz.generate_viz") as mock_generate_viz:
            mock_generate_viz.return_value = '{"label": "test", "type": "root"}'

            # Test the complete workflow
            test_data = {"type": "root", "name": "Test"}
            adapter = AdapterLib.get("3viz")

            result = render(test_data, adapter, "json")

            # Verify the call was made correctly
            mock_generate_viz.assert_called_once_with(
                document_path=test_data,
                adapter_spec=adapter,
                output_format="json",
            )
            assert result == '{"label": "test", "type": "root"}'

    def test_api_backwards_compatibility(self):
        """Test that the API works with file paths (existing CLI behavior)."""
        with patch("treeviz.treeviz.generate_viz") as mock_generate_viz:
            mock_generate_viz.return_value = "file output"

            # This should work exactly like the CLI
            result = render("test.json", "mdast", "text")

            mock_generate_viz.assert_called_once_with(
                document_path="test.json",
                adapter_spec="mdast",
                output_format="text",
            )
            assert result == "file output"
