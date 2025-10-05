"""
Tests for the column layout system.
"""


from treeviz.rendering.layout import ColumnSpec, ColumnAlign, layout_columns
from treeviz.rendering.layout.calculator import calculate_line_layout


class TestColumnSpec:
    """Test ColumnSpec behavior."""

    def test_fixed_width_column(self):
        """Fixed width columns should always return their width."""
        col = ColumnSpec("Hello World", width=5)
        assert col.calculate_width() == 5

    def test_content_width_column(self):
        """Columns without fixed width use content length."""
        col = ColumnSpec("Hello")
        assert col.calculate_width() == 5

    def test_max_width_constraint(self):
        """Max width should limit content width."""
        col = ColumnSpec("Hello World", max_width=5)
        assert col.calculate_width() == 5

    def test_min_width_constraint(self):
        """Min width should expand short content."""
        col = ColumnSpec("Hi", min_width=5)
        assert col.calculate_width() == 5


class TestLayoutColumns:
    """Test the column layout algorithm."""

    def test_single_column(self):
        """Single column should fill available width."""
        columns = [ColumnSpec("Hello", responsive=True)]
        result = layout_columns(columns, 20)
        assert len(result) == 1
        assert len(result[0]) == 20

    def test_fixed_columns_only(self):
        """Fixed columns maintain their sizes."""
        columns = [
            ColumnSpec("A", width=1),
            ColumnSpec("B", width=1),
            ColumnSpec("C", width=1),
        ]
        result = layout_columns(columns, 10)
        assert result == ["A", "B", "C"]

    def test_responsive_column_fills_space(self):
        """Responsive column should take remaining space."""
        columns = [
            ColumnSpec("Icon", width=4),
            ColumnSpec("This is a long label", responsive=True),
            ColumnSpec("5L", width=2),
        ]
        result = layout_columns(columns, 20)
        # 20 - 4 (icon) - 2 (count) - 2 (separators) = 12 for responsive
        assert len(result[1]) == 12

    def test_truncation_with_ellipsis(self):
        """Long content should be truncated with ellipsis."""
        columns = [
            ColumnSpec("This is a very long text", width=10, truncate=True)
        ]
        result = layout_columns(columns, 10)
        assert result[0] == "This is a…"

    def test_right_alignment(self):
        """Right-aligned columns should pad on the left."""
        columns = [ColumnSpec("5L", width=5, align=ColumnAlign.RIGHT)]
        result = layout_columns(columns, 10)
        assert result[0] == "   5L"

    def test_center_alignment(self):
        """Center-aligned columns should pad equally."""
        columns = [ColumnSpec("Hi", width=6, align=ColumnAlign.CENTER)]
        result = layout_columns(columns, 10)
        assert result[0] == "  Hi  "


class TestCalculateLineLayout:
    """Test the convenience line layout function."""

    def test_basic_tree_line(self):
        """Test standard tree line layout."""
        result = calculate_line_layout(
            indent="  ",
            icon="📄",
            label="Document",
            extras="",
            line_count="10L",
            terminal_width=40,
        )
        assert "  📄" in result
        assert "Document" in result
        assert "10L" in result

    def test_long_label_truncation(self):
        """Long labels should be truncated."""
        result = calculate_line_layout(
            indent="",
            icon="📄",
            label="This is a very long document title that should be truncated",
            extras="",
            line_count="1L",
            terminal_width=30,
        )
        assert "…" in result
        assert len(result) <= 30

    def test_with_extras(self):
        """Extras should appear before line count."""
        result = calculate_line_layout(
            indent="  ",
            icon="☰",
            label="List",
            extras="type=ordered",
            line_count="5L",
            terminal_width=50,
        )
        assert "type=ordered" in result
        assert result.index("type=ordered") < result.index("5L")

    def test_deep_indentation(self):
        """Deep indentation should work correctly."""
        result = calculate_line_layout(
            indent="      ",  # 6 spaces
            icon="↵",
            label="Line content",
            extras="",
            line_count="1L",
            terminal_width=40,
        )
        assert result.startswith("      ↵")

    def test_no_icon(self):
        """Lines without icons should work."""
        result = calculate_line_layout(
            indent="  ",
            icon="",
            label="No icon line",
            extras="",
            line_count="1L",
            terminal_width=30,
        )
        assert "  No icon line" in result
