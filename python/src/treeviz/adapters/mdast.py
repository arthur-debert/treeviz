"""
mdast to 3viz Adapter

This module converts an mdast AST into the 3viz data model.
"""

from treeviz.model import Node


class MdastAdapter:
    """
    Adapts an mdast AST to the 3viz data model.
    """

    def adapt(self, mdast_node: dict) -> Node:
        """
        Adapt an mdast node to a Node.
        """
        return self._adapt_node(mdast_node)

    def _adapt_node(self, mdast_node: dict) -> Node:
        """
        Recursively adapt an mdast node to a Node.
        """
        node_type = mdast_node.get("type", "unknown")
        method_name = f"_adapt_{node_type}"
        adapt_method = getattr(self, method_name, self._adapt_generic_node)
        return adapt_method(mdast_node)

    def _adapt_children(self, mdast_node: dict) -> list[Node]:
        """
        Adapt the children of an mdast node.
        """
        children = []
        if "children" in mdast_node:
            for child in mdast_node["children"]:
                children.append(self._adapt_node(child))
        return children

    def _adapt_generic_node(self, mdast_node: dict) -> Node:
        """
        Adapt a generic mdast node.
        """
        text = ""
        if "value" in mdast_node:
            text = str(mdast_node["value"])

        children = self._adapt_children(mdast_node)

        return Node(
            label=text,
            type=mdast_node.get("type", "unknown"),
            children=children,
            content_lines=len(children),
        )

    def _adapt_root(self, mdast_node: dict) -> Node:
        """
        Adapt a root node.
        """
        children = self._adapt_children(mdast_node)
        return Node(
            label="Root",
            type="root",
            children=children,
            content_lines=len(children),
        )

    def _adapt_paragraph(self, mdast_node: dict) -> Node:
        """
        Adapt a paragraph node.
        """
        children = self._adapt_children(mdast_node)
        text = "".join(child.label for child in children)
        return Node(
            label=text,
            type="paragraph",
            children=children,
            content_lines=len(children),
        )

    def _adapt_heading(self, mdast_node: dict) -> Node:
        """
        Adapt a heading node.
        """
        children = self._adapt_children(mdast_node)
        text = "".join(child.label for child in children)
        return Node(
            label=text,
            type="heading",
            children=children,
            metadata={"depth": mdast_node.get("depth")},
            content_lines=len(children),
        )

    def _adapt_list(self, mdast_node: dict) -> Node:
        """
        Adapt a list node.
        """
        children = self._adapt_children(mdast_node)
        return Node(
            label="List",
            type="list",
            children=children,
            metadata={"ordered": mdast_node.get("ordered", False)},
            content_lines=len(children),
        )

    def _adapt_listItem(self, mdast_node: dict) -> Node:
        """
        Adapt a listItem node.
        """
        children = self._adapt_children(mdast_node)
        text = "".join(child.label for child in children)
        return Node(
            label=text,
            type="listItem",
            children=children,
            content_lines=len(children),
        )

    def _adapt_text(self, mdast_node: dict) -> Node:
        """
        Adapt a text node.
        """
        return Node(
            label=mdast_node.get("value", ""),
            type="text",
            content_lines=len(mdast_node.get("value", "")),
        )
