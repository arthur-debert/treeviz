"""
Test the output format constants.
"""

import treeviz
from unittest.mock import patch


class TestOutputConstants:
    """Test that output constants are properly exported and have correct values."""

    def test_output_constants_exist(self):
        """Test that all output constants are exported."""
        assert hasattr(treeviz, "OUTPUT_TEXT")
        assert hasattr(treeviz, "OUTPUT_TERM")
        assert hasattr(treeviz, "OUTPUT_JSON")
        assert hasattr(treeviz, "OUTPUT_YAML")
        assert hasattr(treeviz, "OUTPUT_OBJ")

    def test_output_constants_values(self):
        """Test that output constants have the expected string values."""
        assert treeviz.OUTPUT_TEXT == "text"
        assert treeviz.OUTPUT_TERM == "term"
        assert treeviz.OUTPUT_JSON == "json"
        assert treeviz.OUTPUT_YAML == "yaml"
        assert treeviz.OUTPUT_OBJ == "obj"

    def test_output_constants_usage_with_render(self):
        """Test that output constants work correctly with render function."""
        test_data = {"type": "root", "name": "test"}

        # These should all work without errors
        # (We'll mock generate_viz to avoid actual processing)
        from unittest.mock import patch

        with patch("treeviz.treeviz.generate_viz") as mock_generate_viz:
            mock_generate_viz.return_value = "mocked output"

            # Test each constant
            treeviz.render(test_data, output=treeviz.OUTPUT_TEXT)
            treeviz.render(test_data, output=treeviz.OUTPUT_TERM)
            treeviz.render(test_data, output=treeviz.OUTPUT_JSON)
            treeviz.render(test_data, output=treeviz.OUTPUT_YAML)

            # Verify the constants were passed correctly
            calls = mock_generate_viz.call_args_list
            assert len(calls) == 4
            assert calls[0][1]["output_format"] == "text"
            assert calls[1][1]["output_format"] == "term"
            assert calls[2][1]["output_format"] == "json"
            assert calls[3][1]["output_format"] == "yaml"

    def test_output_obj_constant_calls_generate_viz_directly(self):
        """Test that OUTPUT_OBJ constant calls generate_viz with obj format."""
        test_data = {"type": "root", "name": "test"}

        with patch("treeviz.treeviz.generate_viz") as mock_generate_viz:
            mock_node = treeviz.Node(label="test", type="root", children=[])
            mock_generate_viz.return_value = mock_node

            result = treeviz.render(test_data, output=treeviz.OUTPUT_OBJ)

            # Should call generate_viz with OBJ format directly
            mock_generate_viz.assert_called_once_with(
                document_path=test_data,
                adapter_spec="3viz",
                output_format="obj",
            )

            # Should return the Node object from generate_viz
            assert result is mock_node
            assert isinstance(result, treeviz.Node)
