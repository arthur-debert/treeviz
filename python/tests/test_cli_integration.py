"""
CLI integration tests using real test data.

Tests the end-to-end CLI functionality with actual MDAST and 3viz files.
Maximum 10 tests as per requirements for sanity checking.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIIntegration:
    """Integration tests for CLI with real data files."""

    @pytest.fixture
    def test_data_dir(self):
        """Get the test data directory path."""
        return Path(__file__).parent / "test_data"

    def test_cli_with_real_mdast_json_output(self, test_data_dir):
        """Test CLI with real MDAST file, JSON output."""
        mdast_file = test_data_dir / "mdast" / "simple_document.json"

        # Run CLI command
        result = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(mdast_file),
                "mdast",
                "--output-format",
                "json",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        # Should produce valid JSON
        output_data = json.loads(result.stdout)
        assert output_data["type"] == "root"
        assert len(output_data["children"]) > 0

        # Check that headings are properly converted
        heading = next(
            child
            for child in output_data["children"]
            if child["type"] == "heading"
        )
        assert heading["label"] == "heading"
        # Text content should be in the text child
        text_child = next(
            child for child in heading["children"] if child["type"] == "text"
        )
        assert text_child["label"] == "Simple Document"

    def test_cli_with_real_mdast_term_output(self, test_data_dir):
        """Test CLI with real MDAST file, terminal output."""
        mdast_file = test_data_dir / "mdast" / "real_world_example.json"

        result = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(mdast_file),
                "mdast",
                "--output-format",
                "term",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        # Should contain visual elements
        output = result.stdout
        assert "⧉" in output  # root icon
        assert "⊤" in output  # heading icon
        assert "¶" in output  # paragraph icon
        assert "Getting Started with 3viz" in output
        assert "Features" in output

    def test_cli_with_3viz_format_default(self, test_data_dir):
        """Test CLI with 3viz format file using default adapter."""
        viz_file = test_data_dir / "3viz_simple.json"

        result = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(viz_file),
                "--output-format",
                "term",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        output = result.stdout
        assert "Project Root" in output
        assert "?" in output  # fallback icon for unknown types
        assert "main.py" in output

    def test_cli_with_code_heavy_mdast(self, test_data_dir):
        """Test CLI with code-heavy MDAST example."""
        mdast_file = test_data_dir / "mdast" / "code_heavy_example.json"

        result = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(mdast_file),
                "mdast",
                "--output-format",
                "text",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        output = result.stdout
        assert "Code Examples" in output
        assert "Python Example" in output
        assert "JavaScript Example" in output
        assert "𝒱" in output  # code block icon

    def test_cli_with_stdin_input(self, test_data_dir):
        """Test CLI with stdin input."""
        mdast_file = test_data_dir / "mdast" / "simple_document.json"

        with open(mdast_file) as f:
            mdast_content = f.read()

        result = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                "-",
                "mdast",
                "--output-format",
                "json",
            ],
            input=mdast_content,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        # Should produce same output as file input
        output_data = json.loads(result.stdout)
        assert output_data["type"] == "root"

    def test_cli_yaml_output_format(self, test_data_dir):
        """Test CLI with YAML output format."""
        viz_file = test_data_dir / "3viz_simple.json"

        result = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(viz_file),
                "--output-format",
                "yaml",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        output = result.stdout
        assert "label: Project Root" in output
        assert "type: directory" in output
        assert "children:" in output

    def test_cli_document_format_override(self, test_data_dir):
        """Test CLI with document format override."""
        # Create a .data file with JSON content
        mdast_file = test_data_dir / "mdast" / "simple_document.json"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".data", delete=False
        ) as f:
            with open(mdast_file) as source:
                f.write(source.read())
            f.flush()

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "treeviz",
                    f.name,
                    "mdast",
                    "--document-format",
                    "json",
                    "--output-format",
                    "json",
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent / "src",
            )

        assert result.returncode == 0
        # Allow the expected runpy warning when using -m module execution
        expected_warning = "'treeviz.__main__' found in sys.modules after import of package 'treeviz'"
        if result.stderr and expected_warning not in result.stderr:
            assert result.stderr == "", f"Unexpected stderr: {result.stderr}"

        output_data = json.loads(result.stdout)
        assert output_data["type"] == "root"

    def test_cli_error_handling_missing_file(self):
        """Test CLI error handling for missing file."""
        result = subprocess.run(
            ["python", "-m", "treeviz", "/nonexistent/file.json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode != 0
        assert "Error:" in result.stderr or "Error:" in result.stdout

    def test_cli_error_handling_invalid_adapter(self, test_data_dir):
        """Test CLI error handling for invalid adapter."""
        viz_file = test_data_dir / "3viz_simple.json"

        result = subprocess.run(
            ["python", "-m", "treeviz", str(viz_file), "invalid_adapter"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode != 0
        assert "Error:" in result.stderr or "Error:" in result.stdout

    def test_cli_help_command(self):
        """Test CLI help command works."""
        result = subprocess.run(
            ["python", "-m", "treeviz", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result.returncode == 0
        assert (
            "3viz" in result.stdout.lower()
            or "treeviz" in result.stdout.lower()
        )
        assert (
            "usage" in result.stdout.lower() or "help" in result.stdout.lower()
        )

    def test_cli_theme_override(self, test_data_dir):
        """Test CLI with --theme option."""
        # Use an existing test file
        mdast_file = test_data_dir / "mdast" / "simple_tree.json"

        # Test with dark theme
        result_dark = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(mdast_file),
                "mdast",
                "--output-format", "term",
                "--theme", "dark",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result_dark.returncode == 0
        # Should have ANSI codes
        assert "\x1b[" in result_dark.stdout

        # Test with light theme
        result_light = subprocess.run(
            [
                "python",
                "-m",
                "treeviz",
                str(mdast_file),
                "mdast",
                "--output-format", "term",
                "--theme", "light",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src",
        )

        assert result_light.returncode == 0
        # Should have ANSI codes
        assert "\x1b[" in result_light.stdout
        
        # The outputs should be different due to different color themes
        assert result_dark.stdout != result_light.stdout


class TestCLICornerCases:
    """Additional corner case tests for CLI robustness."""

    @pytest.fixture
    def test_data_dir(self):
        """Get the test data directory path."""
        return Path(__file__).parent / "test_data"

    def test_cli_with_empty_mdast_children(self, test_data_dir):
        """Test CLI handles MDAST with empty children arrays."""
        empty_mdast = {
            "type": "root",
            "children": [{"type": "paragraph", "children": []}],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(empty_mdast, f)
            f.flush()

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "treeviz",
                    f.name,
                    "mdast",
                    "--output-format",
                    "term",
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent / "src",
            )

        assert result.returncode == 0
        # Should handle empty children gracefully
