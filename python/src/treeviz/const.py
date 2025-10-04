from .icon_pack import Icon, IconPack, register_icon_pack

ICONS = {
    # Document structure
    "document": "⧉",
    "session": "§",
    "heading": "⊤",
    "paragraph": "¶",
    "list": "☰",
    "listItem": "•",
    "verbatim": "𝒱",
    "definition": "≔",
    "text": "◦",
    "textLine": "↵",
    "emphasis": "𝐼",
    "strong": "𝐁",
    "inlineCode": "ƒ",
    "contentContainer": "⊡",
    # Data types (for generic JSON/dict structures)
    "dict": "{}",
    "array": "[]",
    "str": '"',
    "int": "#",
    "float": "#",
    "bool": "?",
    "NoneType": "∅",
    # Fallback
    "unknown": "?",
}


DEFAULT_ICONS = {
    "document": Icon(icon="⧉", aliases=["doc", "root"]),
    "session": Icon(icon="§"),
    "heading": Icon(icon="⊤", aliases=["header", "title"]),
    "paragraph": Icon(icon="¶", aliases=["para"]),
    "list": Icon(icon="☰", aliases=["ul", "ol", "list_block"]),
    "listItem": Icon(icon="•", aliases=["li", "list_item_block"]),
    "verbatim": Icon(icon="𝒱", aliases=["code"]),
    "definition": Icon(icon="≔"),
    "text": Icon(icon="◦"),
    "textLine": Icon(icon="↵"),
    "emphasis": Icon(icon="𝐼", aliases=["italic"]),
    "strong": Icon(icon="𝐁", aliases=["bold"]),
    "inlineCode": Icon(icon="ƒ"),
    "contentContainer": Icon(icon="⊡"),
    "dict": Icon(icon="{}"),
    "array": Icon(icon="[]"),
    "str": Icon(icon='"'),
    "int": Icon(icon="#"),
    "float": Icon(icon="#"),
    "bool": Icon(icon="?"),
    "NoneType": Icon(icon="∅"),
    "unknown": Icon(icon="?"),
}

DEFAULT_ICON_PACK = IconPack(name="3viz", icons=DEFAULT_ICONS)

register_icon_pack(DEFAULT_ICON_PACK)
