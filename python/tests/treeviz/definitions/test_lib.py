"""
Unit tests for definition library registry.

Tests the AdapterLib class registry functionality with the new ConfigLoaders system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from treeviz.definitions.lib import AdapterLib
from treeviz.definitions.model import AdapterDef


class TestAdapterLib:
    """Test the new AdapterLib with ConfigLoaders."""

    def setup_method(self):
        """Clear cache before each test."""
        AdapterLib.clear()

    def test_get_3viz_returns_default(self):
        """Test that getting '3viz' returns default AdapterDef."""
        adapter = AdapterLib.get("3viz")
        assert isinstance(adapter, AdapterDef)
        # Default should have standard values
        assert adapter.label == "label"
        assert adapter.type == "type"
        assert adapter.children == "children"
        # Should have default icons
        assert "document" in adapter.icons
        assert adapter.icons["document"] == "⧉"

    def test_get_caches_results(self):
        """Test that adapters are cached after first load."""
        # Mock the loaders to track calls
        with patch.object(AdapterLib, "_loaders") as mock_loaders:
            mock_loaders.load_adapter.return_value = AdapterDef(label="test")

            # First call should load from loaders
            adapter1 = AdapterLib.get("test_format")
            assert mock_loaders.load_adapter.called

            # Reset mock
            mock_loaders.load_adapter.reset_mock()

            # Second call should use cache
            adapter2 = AdapterLib.get("test_format")
            assert not mock_loaders.load_adapter.called
            assert adapter1 is adapter2

    def test_get_unknown_format_raises_keyerror(self):
        """Test that getting unknown format raises KeyError."""
        with patch.object(AdapterLib, "_loaders") as mock_loaders:
            mock_loaders.load_adapter.return_value = None
            mock_loaders.get_adapter_names.return_value = ["mdast", "unist"]

            with pytest.raises(KeyError) as exc_info:
                AdapterLib.get("unknown_format")

            error_msg = str(exc_info.value)
            assert "unknown_format" in error_msg
            assert "Available formats" in error_msg
            assert "mdast" in error_msg

    def test_list_formats_includes_3viz(self):
        """Test that list_formats always includes '3viz'."""
        with patch.object(AdapterLib, "_loaders") as mock_loaders:
            mock_loaders.get_adapter_names.return_value = []

            formats = AdapterLib.list_formats()
            assert "3viz" in formats

    def test_list_formats_includes_loaded_adapters(self):
        """Test that list_formats includes adapters from loaders."""
        with patch.object(AdapterLib, "_loaders") as mock_loaders:
            mock_loaders.get_adapter_names.return_value = [
                "mdast",
                "unist",
                "pandoc",
            ]

            formats = AdapterLib.list_formats()
            assert "3viz" in formats
            assert "mdast" in formats
            assert "unist" in formats
            assert "pandoc" in formats
            # Should be sorted
            assert formats == sorted(formats)

    def test_ensure_all_loaded_initializes_loaders(self):
        """Test that ensure_all_loaded ensures loaders are initialized."""
        AdapterLib._loaders = None
        AdapterLib.ensure_all_loaded()
        assert AdapterLib._loaders is not None

    def test_clear_clears_cache_and_loaders(self):
        """Test that clear() clears both cache and loaders."""
        # Set up some state
        AdapterLib._cache["test"] = AdapterDef(label="test")
        AdapterLib._loaders = MagicMock()

        AdapterLib.clear()

        assert len(AdapterLib._cache) == 0
        assert AdapterLib._loaders is None

    def test_clear_cache_only_clears_cache(self):
        """Test that clear_cache() only clears cache, not loaders."""
        # Set up some state
        AdapterLib._cache["test"] = AdapterDef(label="test")
        AdapterLib._loaders = MagicMock()

        AdapterLib.clear_cache()

        assert len(AdapterLib._cache) == 0
        assert AdapterLib._loaders is not None  # Should still be set


class TestAdapterLibIntegration:
    """Integration tests with actual ConfigLoaders."""

    def setup_method(self):
        """Clear cache before each test."""
        AdapterLib.clear()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up temp directory."""
        self.temp_dir.cleanup()
        AdapterLib.clear()

    def test_loads_builtin_adapters(self):
        """Test that built-in adapters can be loaded."""
        # Should be able to get built-in adapters
        formats = AdapterLib.list_formats()

        # Check some expected built-ins exist
        assert "3viz" in formats
        # Might have other built-ins like mdast, unist, etc.
        assert len(formats) >= 1
