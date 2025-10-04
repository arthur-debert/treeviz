import pytest
from treeviz.adapters.core import adapt_node
from treeviz.icon_pack import register_icon_pack, IconPack, Icon


# Sample AST node for testing
class SimpleNode:
    def __init__(self, type, children=None):
        self.type = type
        self.children = children or []


@pytest.fixture(autouse=True)
def cleanup_icon_registry():
    """
    Fixture to clean up the icon registry after each test.
    """
    # This is a bit of a hack, but it's the easiest way to ensure a clean slate for each test
    from treeviz.icon_pack import _ICON_PACK_REGISTRY

    _ICON_PACK_REGISTRY.clear()
    # Re-register the default pack
    from treeviz.const import DEFAULT_ICON_PACK

    register_icon_pack(DEFAULT_ICON_PACK)


def test_direct_icon_mapping():
    """Test that a direct icon mapping in the adapter def works."""
    node = SimpleNode("custom_type")
    def_ = {"icons": {"custom_type": "💡"}}
    result = adapt_node(node, def_)
    assert result.icon == "💡"


def test_default_pack_fallback():
    """Test that the default 'treeviz' pack is used when no mapping is provided."""
    node = SimpleNode("heading")
    def_ = {}
    result = adapt_node(node, def_)
    assert result.icon == "⊤"


def test_default_pack_alias_fallback():
    """Test that an alias in the default 'treeviz' pack is resolved."""
    node = SimpleNode("para")
    def_ = {}
    result = adapt_node(node, def_)
    assert result.icon == "¶"


def test_custom_default_pack():
    """Test setting a custom default pack for the adapter."""
    custom_pack = IconPack(
        name="custom", icons={"custom_type": Icon(icon="🎉")}
    )
    register_icon_pack(custom_pack)
    node = SimpleNode("custom_type")
    def_ = {"icons": {"": "custom"}}
    result = adapt_node(node, def_)
    assert result.icon == "🎉"


def test_specific_pack_and_icon_reference():
    """Test referencing a specific icon from a specific pack."""
    custom_pack = IconPack(name="custom", icons={"my_icon": Icon(icon="🚀")})
    register_icon_pack(custom_pack)
    node = SimpleNode("my_node")
    def_ = {"icons": {"my_node": "custom.my_icon"}}
    result = adapt_node(node, def_)
    assert result.icon == "🚀"


def test_pack_reference_fallback_to_default_pack():
    """Test that if an icon is not in the specified pack, it falls back to the default pack."""
    custom_pack = IconPack(name="custom", icons={})
    register_icon_pack(custom_pack)
    node = SimpleNode("my_node")
    # "heading" is in the default pack, but not in "custom"
    def_ = {"icons": {"my_node": "custom.heading"}}
    result = adapt_node(node, def_)
    assert result.icon == "⊤"


def test_user_defined_icon_pack_in_adapter():
    """Test defining and using an icon pack directly in the adapter definition."""
    node = SimpleNode("user_node")
    def_ = {
        "ICON_PACKS": [
            {
                "name": "user_pack",
                "icons": {
                    "user_icon": {"icon": "🌟", "aliases": ["user_node"]},
                },
            }
        ],
        "icons": {"": "user_pack"},
    }
    result = adapt_node(node, def_)
    assert result.icon == "🌟"


def test_invalid_icon_pack_name_in_adapter():
    """Test that an icon pack with an invalid name is rejected."""
    with pytest.raises(
        ValueError, match="Icon pack name 'invalid.pack' is not valid."
    ):
        adapt_node(
            SimpleNode("a"),
            {"ICON_PACKS": [{"name": "invalid.pack", "icons": {}}]},
        )


def test_invalid_icon_name_in_adapter():
    """Test that an icon with an invalid name is rejected."""
    with pytest.raises(
        ValueError, match="Icon name 'invalid-icon' is not a valid identifier."
    ):
        adapt_node(
            SimpleNode("a"),
            {
                "ICON_PACKS": [
                    {
                        "name": "user_pack",
                        "icons": {"invalid-icon": {"icon": "X"}},
                    }
                ]
            },
        )


def test_mixed_mode_icons():
    """Test mixing direct icons, pack references, and a default pack."""
    custom_pack = IconPack(name="custom", icons={"icon2": Icon(icon="B")})
    register_icon_pack(custom_pack)

    def_ = {
        "icons": {
            "type1": "A",
            "type2": "custom.icon2",
            "": "treeviz",
        }
    }

    assert adapt_node(SimpleNode("type1"), def_).icon == "A"
    assert adapt_node(SimpleNode("type2"), def_).icon == "B"
    assert (
        adapt_node(SimpleNode("heading"), def_).icon == "⊤"
    )  # From treeviz pack
    assert (
        adapt_node(SimpleNode("para"), def_).icon == "¶"
    )  # Alias from treeviz pack
