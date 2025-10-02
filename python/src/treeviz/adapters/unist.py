"""
Unist to 3viz Adapter

This module converts a unist AST into the 3viz data model.
"""

from treeviz.model import Node


class UnistAdapter:
    """
    Adapts a unist AST to the 3viz data model.
    """

    def adapt(self, unist_node: dict) -> Node:
        """
        Adapt a unist node to a Node.
        """
        return self._adapt_node(unist_node)

    def _adapt_node(self, unist_node: dict) -> Node:
        """
        Recursively adapt a unist node to a Node.
        """
        node_type = unist_node.get("type", "unknown")

        text = ""
        if "value" in unist_node:
            text = str(unist_node["value"])
        elif (
            "children" in unist_node
            and len(unist_node["children"]) > 0
            and "value" in unist_node["children"][0]
        ):
            # For parent nodes, try to get text from children
            text = "".join(
                str(child.get("value", "")) for child in unist_node["children"]
            )

        children = []
        if "children" in unist_node:
            for child in unist_node["children"]:
                children.append(self._adapt_node(child))

        return Node(
            label=text,
            type=node_type,
            children=children,
            content_lines=len(children),
        )
