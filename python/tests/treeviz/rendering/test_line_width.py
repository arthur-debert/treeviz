"""
Tests for line width constraints in rendering.
"""

from pathlib import Path
from treeviz.viz import generate_viz


def assert_no_lines_exceed_width(render_result: str, terminal_width: int):
    """
    Custom assertion that checks no lines in the render output exceed the specified width.

    Args:
        render_result: The rendered string output from treeviz
        terminal_width: The maximum allowed width for any line

    Raises:
        AssertionError: If any lines exceed the terminal width, with details about violations
    """
    lines = render_result.split("\n")

    # Track problematic lines for detailed error reporting
    violations = []
    for line_num, line in enumerate(lines, 1):
        line_length = len(line)
        if line_length > terminal_width:
            violations.append(
                {
                    "line_num": line_num,
                    "length": line_length,
                    "content": line,
                    "excess": line_length - terminal_width,
                }
            )

    if violations:
        # Create a detailed error message
        error_parts = [
            f"Found {len(violations)} line(s) exceeding {terminal_width} characters:"
        ]

        for violation in violations:
            error_parts.append(
                f"  Line {violation['line_num']}: {violation['length']} chars "
                f"(+{violation['excess']} over limit)"
            )
            error_parts.append(f"    Content: '{violation['content']}'")

        error_parts.append(f"\nTotal lines checked: {len(lines)}")
        error_parts.append(f"Terminal width limit: {terminal_width}")

        raise AssertionError("\n".join(error_parts))


def assert_treeviz_output_format(
    render_result: str, terminal_width: int, indent_size: int = 2
):
    """
    Custom assertion that validates the general format of treeviz output.

    Args:
        render_result: The rendered string output from treeviz
        terminal_width: The maximum allowed width for any line
        indent_size: Number of spaces per indentation level (default: 2)

    Raises:
        AssertionError: If the output format doesn't match expected treeviz structure
    """
    lines = render_result.split("\n")

    violations = []

    for line_num, line in enumerate(lines, 1):
        # Skip empty lines
        if not line.strip():
            continue

        # Check line width
        if len(line) > terminal_width:
            violations.append(
                f"Line {line_num}: Exceeds terminal width ({len(line)} > {terminal_width})"
            )
            continue

        # Check indentation (must be multiple of indent_size)
        leading_spaces = len(line) - len(line.lstrip(" "))
        if leading_spaces % indent_size != 0:
            violations.append(
                f"Line {line_num}: Invalid indentation ({leading_spaces} spaces, should be multiple of {indent_size})"
            )
            continue

        stripped_line = line.lstrip(" ")

        # Must have at least: icon + space + content + space + linecount
        if len(stripped_line) < 4:
            violations.append(
                f"Line {line_num}: Line too short to contain required elements"
            )
            continue

        # First character should be a valid icon (Unicode character)
        icon = stripped_line[0]
        if not icon or icon.isspace():
            violations.append(
                f"Line {line_num}: Missing or invalid icon at start"
            )
            continue

        # Second character must be a space
        if len(stripped_line) < 2 or stripped_line[1] != " ":
            violations.append(
                f"Line {line_num}: Icon must be followed by space"
            )
            continue

        # Line should end with line count format (digits followed by 'L')
        if not stripped_line.endswith("L"):
            violations.append(
                f"Line {line_num}: Line should end with line count format (e.g., '1L', '12L')"
            )
            continue

        # Extract the line count part (everything after the last space before 'L')
        line_count_match = None
        for i in range(len(stripped_line) - 1, -1, -1):
            if stripped_line[i] == " ":
                potential_count = stripped_line[i + 1 :]
                if (
                    potential_count.endswith("L")
                    and potential_count[:-1].isdigit()
                ):
                    line_count_match = potential_count
                    break

        if not line_count_match:
            violations.append(
                f"Line {line_num}: Invalid line count format at end"
            )
            continue

    if violations:
        error_parts = [
            f"Found {len(violations)} format violation(s) in treeviz output:"
        ]
        error_parts.extend(f"  {violation}" for violation in violations)
        error_parts.append(
            f"\nExpected format: [N*{indent_size} spaces][icon][ ][content][ ][digits]L"
        )
        error_parts.append(f"Terminal width: {terminal_width}")
        error_parts.append(
            f"Total lines checked: {len([line for line in lines if line.strip()])}"
        )

        raise AssertionError("\n".join(error_parts))


class TestLineWidth:
    """Test that rendered output respects terminal width constraints."""

    def test_verbatim_file_line_width_constraint(self):
        """Test that the verbatim-simple.3viz.json file renders with all lines < 80 chars."""
        # Path to the test file - go up to project root then to test-docs
        project_root = Path(__file__).parent.parent.parent.parent.parent
        test_file = (
            project_root
            / "test-docs"
            / "elements"
            / "verbatim"
            / "verbatim-simple.3viz.json"
        )

        # Verify the file exists
        assert test_file.exists(), f"Test file not found: {test_file}"

        # Render with explicit terminal width of 80
        terminal_width = 80
        result = generate_viz(
            document_path=str(test_file),
            adapter_spec="3viz",
            document_format="json",
            output_format="text",  # Use text format to avoid color codes
            terminal_width=terminal_width,
        )

        # Use comprehensive format assertion
        assert_treeviz_output_format(result, terminal_width)

        # Additional check: ensure we actually have content
        lines = result.split("\n")
        assert len(lines) > 10, "Expected substantial output from the test file"

    def test_deeply_nested_content_width(self):
        """Test that deeply nested content still respects width constraints."""
        from treeviz.model import Node

        # Create deeply nested content to test per-line width calculation
        deep_node = Node(
            label="Root with a very long label that should be truncated appropriately",
            type="document",
            children=[
                Node(
                    label="Level 1 with an even longer label that definitely needs truncation to fit within constraints",
                    type="section",
                    children=[
                        Node(
                            label="Level 2 with yet another extremely long label that must be truncated for proper alignment and width",
                            type="paragraph",
                            children=[
                                Node(
                                    label="Level 3 deeply nested with maximum length label that tests the per-line width calculation thoroughly",
                                    type="text",
                                )
                            ],
                        )
                    ],
                )
            ],
        )

        terminal_width = 80
        result = generate_viz(
            document_path=deep_node,
            adapter_spec="3viz",
            output_format="text",
            terminal_width=terminal_width,
        )

        # Use comprehensive format assertion
        assert_treeviz_output_format(result, terminal_width)

    def test_various_terminal_widths(self):
        """Test that the renderer respects different terminal widths."""
        from treeviz.model import Node

        # Create a test node with long content
        test_node = Node(
            label="This is a test node with a moderately long label to test width constraints",
            type="document",
            children=[
                Node(
                    label="Child with another long label that should be truncated based on available space",
                    type="paragraph",
                )
            ],
        )

        # Test different terminal widths
        for width in [40, 60, 80, 120]:
            result = generate_viz(
                document_path=test_node,
                adapter_spec="3viz",
                output_format="text",
                terminal_width=width,
            )

            # Use comprehensive format assertion for each width
            assert_treeviz_output_format(result, width)

    def test_treeviz_output_format_validation(self):
        """Test comprehensive format validation of treeviz output."""
        from treeviz.model import Node

        # Create a test case with various node types and nesting levels
        test_node = Node(
            label="Root Document",
            type="document",
            extra={"type": "test", "version": "1.0"},
            children=[
                Node(
                    label="Section with extras",
                    type="section",
                    extra={"level": 1, "numbered": True},
                    children=[
                        Node(
                            label="Paragraph content",
                            type="paragraph",
                            children=[
                                Node(
                                    label="Text content with some length",
                                    type="text",
                                ),
                                Node(label="Another text node", type="text"),
                            ],
                        ),
                        Node(
                            label="Verbatim code block\nwith multiple lines\nand formatting",
                            type="verbatim",
                            extra={"language": "python"},
                        ),
                    ],
                )
            ],
        )

        terminal_width = 80
        result = generate_viz(
            document_path=test_node,
            adapter_spec="3viz",
            output_format="text",
            terminal_width=terminal_width,
        )

        # This should validate:
        # 1. Terminal width compliance
        # 2. Proper indentation (multiples of 2)
        # 3. Icon + space format
        # 4. Line count format at end
        assert_treeviz_output_format(result, terminal_width, indent_size=2)

        # Also ensure we have the expected structure
        lines = [line for line in result.split("\n") if line.strip()]
        assert len(lines) >= 6, "Should have multiple nested levels"

        # Check that we have different indentation levels
        indentation_levels = set()
        for line in lines:
            leading_spaces = len(line) - len(line.lstrip(" "))
            indentation_levels.add(leading_spaces)

        assert (
            len(indentation_levels) >= 3
        ), "Should have at least 3 different indentation levels"
        assert 0 in indentation_levels, "Should have root level (0 spaces)"
