"""
Unit tests for renderer output format validation.

These tests verify the exact spacing, alignment, and truncation behavior
of the renderer without needing full integration tests.
"""

import re
from treeviz.model import Node
from treeviz.rendering.engines.template import TemplateRenderer


class TestRendererFormat:
    """Test exact renderer output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = TemplateRenderer()
        # Standard test options
        # Import default symbols for testing
        from treeviz.const import ICONS

        self.options = {
            "symbols": ICONS,
            "terminal_width": 80,
            "format": "text",
        }

    def test_single_space_after_icon(self):
        """Test that there's always exactly one space between icon and label."""
        # Create nodes at different depths
        root = Node(
            label="Root",
            type="document",
            children=[
                Node(
                    label="Level 1",
                    type="paragraph",
                    children=[
                        Node(
                            label="Level 2 with longer text",
                            type="text",
                            children=[Node(label="Level 3", type="text")],
                        )
                    ],
                )
            ],
        )

        result = self.renderer.render(root, self.options)
        lines = result.strip().split("\n")

        # Check each line for proper spacing
        # Pattern: (optional indent)(icon)(exactly one space)(label)
        for line in lines:
            # Extract parts using regex
            match = re.match(r"^(\s*)(\S)(\s+)(.+?)(\s+)(\d+L)$", line)
            assert match, f"Line doesn't match expected format: {line}"

            indent, icon, space_after_icon, label, padding, line_count = (
                match.groups()
            )

            # Verify exactly one space after icon
            assert (
                space_after_icon == " "
            ), f"Expected 1 space after icon, got {len(space_after_icon)}: '{line}'"

    def test_indentation_levels(self):
        """Test that indentation is exactly 2 spaces per level."""
        root = Node(
            label="Root",
            children=[
                Node(
                    label="L1",
                    children=[Node(label="L2", children=[Node(label="L3")])],
                )
            ],
        )

        result = self.renderer.render(root, self.options)
        lines = result.strip().split("\n")

        expected_indents = [
            ("Root", 0),
            ("L1", 2),
            ("L2", 4),
            ("L3", 6),
        ]

        for line, (expected_label, expected_indent) in zip(
            lines, expected_indents
        ):
            match = re.match(r"^(\s*)", line)
            indent = match.group(1)
            assert (
                len(indent) == expected_indent
            ), f"Expected {expected_indent} spaces for '{expected_label}', got {len(indent)}"
            assert expected_label in line

    def test_line_count_right_alignment(self):
        """Test that line counts are right-aligned."""
        nodes = [
            Node(label="Single digit", content_lines=1),
            Node(label="Double digit", content_lines=10),
            Node(label="Triple digit", content_lines=100),
            Node(
                label="With children",
                children=[Node(label="C1"), Node(label="C2")],
            ),
        ]

        for node in nodes:
            result = self.renderer.render(node, self.options)
            lines = result.strip().split("\n")

            # Check that line count is at the end and right-aligned
            for line in lines:
                # Line should end with digits followed by 'L'
                match = re.search(r"(\s+)(\d+L)$", line)
                assert match, f"Line doesn't end with line count: {line}"

                # Verify it's at the expected position (right edge)
                assert len(line) <= 80, f"Line exceeds terminal width: {line}"

    def test_label_truncation_cases(self):
        """Test various label truncation scenarios."""
        test_cases = [
            # (label, terminal_width, expected_contains, should_have_ellipsis)
            ("Short label", 80, "Short label", False),
            (
                "This is a very long label that should be truncated with ellipsis when it exceeds available space",
                50,
                "This is",
                True,
            ),
            (
                "Exact fit test",
                30,
                "Exact fit test",
                False,
            ),  # Actually fits at width 30
            (
                "A much longer label that definitely won't fit in narrow terminal",
                30,
                "A much",
                True,
            ),
            ("", 80, "", False),  # Empty label
        ]

        for label, width, expected_contains, should_have_ellipsis in test_cases:
            node = Node(label=label, type="text")
            options = self.options.copy()
            options["terminal_width"] = width

            result = self.renderer.render(node, options)

            assert (
                expected_contains in result or label == ""
            ), f"Expected '{expected_contains}' in result: {result}"
            if should_have_ellipsis:
                assert (
                    "…" in result
                ), f"Expected ellipsis for truncated label: {result}"
            else:
                assert "…" not in result, f"Unexpected ellipsis: {result}"

    def test_label_truncation_with_extras(self):
        """Test label truncation when extras are present."""
        # Long label with extras should truncate label, not extras
        node = Node(
            label="This is a very long label that needs truncation",
            type="text",
            extra={"type": "ordered", "start": 1},
        )

        options = self.options.copy()
        options["terminal_width"] = 60

        result = self.renderer.render(node, options)

        # Extras should be visible
        assert "type=ordered" in result
        # Label should be truncated
        assert "…" in result
        # Full label should not be present
        assert "needs truncation" not in result

    def test_extras_truncation(self):
        """Test that extras are truncated at 20 chars."""
        node = Node(
            label="Test",
            type="text",
            extra={
                "very_long_key": "with_very_long_value_that_exceeds_twenty_chars"
            },
        )

        result = self.renderer.render(node, self.options)

        # Extract the extras part
        match = re.search(r"Test\s+(.*?)\s+\d+L", result)
        assert match, "Could not find extras in output"

        extras = match.group(1).strip()
        assert (
            len(extras) <= 20
        ), f"Extras should be max 20 chars, got {len(extras)}: '{extras}'"
        assert extras.endswith("…"), "Long extras should end with ellipsis"

    def test_complex_tree_spacing(self):
        """Test spacing in a complex tree with mixed content."""
        root = Node(
            label="Document",
            type="document",
            children=[
                Node(
                    label="Section 1",
                    type="heading",
                    children=[
                        Node(
                            label="- That's right Ma and this is true",
                            type="text",
                        ),
                        Node(
                            label="Another line",
                            type="text",
                            extra={"note": "test"},
                        ),
                    ],
                ),
                Node(
                    label="Section 2",
                    type="heading",
                    extra={"level": 2},
                    children=[Node(label="Content here", type="paragraph")],
                ),
            ],
        )

        result = self.renderer.render(root, self.options)
        lines = result.strip().split("\n")

        # Verify each line
        for i, line in enumerate(lines):
            # Check spacing pattern
            match = re.match(
                r"^(\s*)(\S)(\s+)(.+?)(?:\s+([\w=]+\s*)+)?(\s+)(\d+L)$", line
            )
            if not match:
                # Try without extras
                match = re.match(r"^(\s*)(\S)(\s+)(.+?)(\s+)(\d+L)$", line)

            assert match, f"Line {i} doesn't match expected format: '{line}'"

            groups = match.groups()
            icon_space = groups[2]
            assert (
                icon_space == " "
            ), f"Line {i}: Expected 1 space after icon, got {len(icon_space)}"

    def test_empty_children_list(self):
        """Test nodes with empty children list."""
        node = Node(label="Empty parent", children=[], content_lines=0)
        result = self.renderer.render(node, self.options)

        # Should show 0L for no children when content_lines is explicitly 0
        assert "0L" in result

        # Default behavior: empty children with default content_lines=1
        node2 = Node(label="Default empty", children=[])
        result2 = self.renderer.render(node2, self.options)
        assert "1L" in result2  # Default content_lines is 1

    def test_custom_icon_rendering(self):
        """Test that custom icons are used correctly."""
        node = Node(label="Custom", type="custom", icon="★")  # Custom icon

        result = self.renderer.render(node, self.options)
        assert "★ Custom" in result

        # Verify spacing after custom icon
        match = re.match(r"^(\S)(\s+)(.*?)\s+\d+L$", result.strip())
        assert match
        assert (
            match.group(2) == " "
        ), "Custom icon should have one space after it"

    def test_unicode_icon_spacing(self):
        """Test spacing with multi-byte Unicode icons."""
        # Some Unicode characters may display wider but should still have 1 space
        unicode_icons = ["𝐁", "𝐼", "⧉", "№", "𝒱", "≔"]

        for icon in unicode_icons:
            node = Node(label=f"Test with {icon}", icon=icon)
            result = self.renderer.render(node, self.options)

            # Extract spacing after icon
            match = re.match(rf"^{re.escape(icon)}(\s+)", result)
            assert match, f"Could not match icon {icon}"
            assert (
                match.group(1) == " "
            ), f"Icon {icon} should have exactly 1 space after it"

    def test_dash_label_spacing(self):
        """Test the specific case with dash in label."""
        # This reproduces the exact issue reported
        root = Node(
            label="Root",
            children=[
                Node(
                    label="- That's right Ma and this is true for any end-punctuatio ( ?., !., !!., ??., ....)",
                    type="paragraph",
                    icon="¶",
                )
            ],
        )

        result = self.renderer.render(root, self.options)
        lines = result.strip().split("\n")

        # Find the line with the dash
        dash_line = None
        for line in lines:
            if "- That's right Ma" in line:
                dash_line = line
                break

        assert dash_line, "Could not find the dash line"

        # Debug output
        print(f"\nDash line: '{dash_line}'")
        print(f"Line repr: {repr(dash_line)}")

        # Extract the spacing between icon and dash
        match = re.search(r"¶(\s+)-", dash_line)
        assert (
            match
        ), f"Could not find ¶ followed by spaces and dash in: '{dash_line}'"

        spaces = match.group(1)
        print(f"Spaces between ¶ and -: {len(spaces)} ('{spaces}')")

        assert (
            len(spaces) == 1
        ), f"Expected 1 space between ¶ and -, got {len(spaces)}"

    def test_label_with_leading_spaces(self):
        """Test what happens when label has leading spaces."""
        # Maybe the issue is that the label itself starts with spaces?
        root = Node(
            label="Root",
            children=[
                Node(
                    # Label that starts with spaces before the dash
                    label="     - That's right Ma and this is true",
                    type="paragraph",
                    icon="¶",
                )
            ],
        )

        result = self.renderer.render(root, self.options)
        lines = result.strip().split("\n")

        # Find the line with spaces
        target_line = None
        for line in lines:
            if "That's right Ma" in line:
                target_line = line
                break

        assert target_line, "Could not find the target line"

        print(f"\nTarget line: '{target_line}'")
        print(f"Line repr: {repr(target_line)}")

        # Check if label preserved the leading spaces
        # This might be the source of the issue - labels with leading whitespace
        if "¶     -" in target_line:
            print(
                "FOUND THE ISSUE: Label has leading spaces that are being preserved!"
            )

        # The label should be trimmed or the spaces should be normalized
        match = re.search(r"¶(\s+)", target_line)
        assert match, "Could not find ¶ followed by spaces"

        spaces_after_icon = match.group(1)
        print(
            f"Spaces after ¶: {len(spaces_after_icon)} ('{spaces_after_icon}')"
        )

        # After fix, there should only be 1 space
        assert (
            len(spaces_after_icon) == 1
        ), f"Label leading spaces should be stripped, expected 1 space after icon, got {len(spaces_after_icon)}"
