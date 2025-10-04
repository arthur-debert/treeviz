"""
Tests for filter transformation consistency.

This module tests the deprecation of top-level filter key in favor of
the filter transformation within the transform pipeline.
"""

import logging
from treeviz.adapters.extraction.engine import extract_attribute


class TestFilterConsistency:
    """Test filter transformation consistency and deprecation."""

    def test_top_level_filter_deprecation_warning(self, caplog):
        """Test that top-level filter key triggers deprecation warning."""
        source_node = {
            "content": [
                {"t": "Str", "c": "hello"},
                {"t": "Space", "c": " "},
                {"t": "Str", "c": "world"},
            ]
        }

        extraction_spec = {
            "path": "content",  # Get the content list
            "filter": {"t": "Str"},  # Top-level filter (deprecated)
        }

        with caplog.at_level(logging.WARNING):
            result = extract_attribute(source_node, extraction_spec)

        # Should get filtered result
        expected = [{"t": "Str", "c": "hello"}, {"t": "Str", "c": "world"}]
        assert result == expected

        # Should have deprecation warning
        assert "Top-level 'filter' key is deprecated" in caplog.text
        assert "transform pipeline instead" in caplog.text

    def test_pipeline_filter_no_warning(self, caplog):
        """Test that pipeline filter doesn't trigger deprecation warning."""
        source_node = {
            "content": [
                {"t": "Str", "c": "hello"},
                {"t": "Space", "c": " "},
                {"t": "Str", "c": "world"},
            ]
        }

        extraction_spec = {
            "path": "content",  # Get the content list
            "transform": [
                {"name": "filter", "t": "Str"}  # Pipeline filter (recommended)
            ],
        }

        with caplog.at_level(logging.WARNING):
            result = extract_attribute(source_node, extraction_spec)

        # Should get filtered result
        expected = [{"t": "Str", "c": "hello"}, {"t": "Str", "c": "world"}]
        assert result == expected

        # Should NOT have deprecation warning
        assert "deprecated" not in caplog.text

    def test_both_approaches_equivalent_results(self):
        """Test that both filter approaches produce identical results."""
        source_node = {
            "items": [
                {"type": "text", "value": "hello", "length": 5},
                {"type": "space", "value": " ", "length": 1},
                {"type": "text", "value": "world", "length": 5},
                {"type": "punct", "value": "!", "length": 1},
            ]
        }

        # Top-level filter approach (deprecated)
        deprecated_spec = {"path": "items", "filter": {"type": "text"}}

        # Pipeline filter approach (recommended)
        pipeline_spec = {
            "path": "items",
            "transform": [{"name": "filter", "type": "text"}],
        }

        deprecated_result = extract_attribute(source_node, deprecated_spec)
        pipeline_result = extract_attribute(source_node, pipeline_spec)

        # Results should be identical
        assert deprecated_result == pipeline_result

        expected = [
            {"type": "text", "value": "hello", "length": 5},
            {"type": "text", "value": "world", "length": 5},
        ]
        assert deprecated_result == expected

    def test_pipeline_filter_more_flexible(self):
        """Test that pipeline filter can be combined with other transforms."""
        source_node = {
            "tokens": [
                {"type": "text", "value": "HELLO"},
                {"type": "space", "value": " "},
                {"type": "text", "value": "WORLD"},
                {"type": "punct", "value": "!"},
            ]
        }

        # Complex pipeline: filter then extract values then join
        pipeline_spec = {
            "path": "tokens",
            "transform": [
                {"name": "filter", "type": "text"},  # Filter to text nodes
                {
                    "name": "extract",
                    "field": "value",
                },  # Extract values: ["HELLO", "WORLD"]
                {"name": "join", "separator": " "},  # Join: "HELLO WORLD"
            ],
        }

        result = extract_attribute(source_node, pipeline_spec)
        assert result == "HELLO WORLD"

        # This flexibility isn't possible with top-level filter
        # because it can only filter, not transform further

    def test_multiple_filter_conditions(self):
        """Test filtering with multiple conditions."""
        source_node = {
            "data": [
                {"type": "text", "lang": "en", "value": "hello"},
                {"type": "text", "lang": "es", "value": "hola"},
                {"type": "space", "lang": "en", "value": " "},
                {"type": "text", "lang": "en", "value": "world"},
            ]
        }

        # Filter by multiple conditions
        pipeline_spec = {
            "path": "data",
            "transform": [{"name": "filter", "type": "text", "lang": "en"}],
        }

        result = extract_attribute(source_node, pipeline_spec)

        expected = [
            {"type": "text", "lang": "en", "value": "hello"},
            {"type": "text", "lang": "en", "value": "world"},
        ]
        assert result == expected

    def test_filter_preserves_order(self):
        """Test that filtering preserves the original order."""
        source_node = {
            "records": [
                {"id": 1, "active": True},
                {"id": 2, "active": False},
                {"id": 3, "active": True},
                {"id": 4, "active": False},
                {"id": 5, "active": True},
            ]
        }

        pipeline_spec = {
            "path": "records",
            "transform": [{"name": "filter", "active": True}],
        }

        result = extract_attribute(source_node, pipeline_spec)

        expected = [
            {"id": 1, "active": True},
            {"id": 3, "active": True},
            {"id": 5, "active": True},
        ]
        assert result == expected

        # Verify order is preserved
        ids = [item["id"] for item in result]
        assert ids == [1, 3, 5]
