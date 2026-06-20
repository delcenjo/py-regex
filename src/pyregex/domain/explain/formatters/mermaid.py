# src/pyregex/domain/explain/formatters/mermaid.py
from __future__ import annotations
from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    LiteralNode,
    DotNode,
    AlternationNode,
    GroupNode,
    QuantifierNode,
)


class MermaidFormatter:
    """Generates a Mermaid state graph (Flowchart) from a Regex AST."""

    def __init__(self, root: RootNode):
        self.root = root
        self._node_id_counter = 0

    def format(self) -> str:
        """Returns the complete Mermaid diagram text."""
        lines = ["graph TD"]
        lines.append("    Start((Start))")
        lines.append("    End((End))")

        last_id = "Start"

        for child in self.root.children:
            curr_start, curr_end = self._build_node(child, lines)
            lines.append(f"    {last_id} --> {curr_start}")
            last_id = curr_end

        lines.append(f"    {last_id} --> End")
        return "\n".join(lines)

    def _get_id(self) -> str:
        self._node_id_counter += 1
        return f"node_{self._node_id_counter}"

    def _build_node(self, node: AstNode, lines: list[str]) -> tuple[str, str]:
        """Returns the (entrance_id, exit_id) of the subgraph snippet it generated."""
        my_id = self._get_id()

        if isinstance(node, LiteralNode):
            val = node.value.replace('"', '\\"').replace("(", "\\(").replace(")", "\\)")
            lines.append(f"    {my_id}[\"'{val}'\"]")
            return my_id, my_id

        if isinstance(node, DotNode):
            lines.append(f'    {my_id}["[Any Character]"]')
            return my_id, my_id

        if isinstance(node, QuantifierNode):
            # Represent loop
            lines.append(
                f'    {my_id}{{ "Loop [{node.min}, {node.max if node.max else "∞"}]" }}'
            )
            child_start, child_end = self._build_node(node.child, lines)
            lines.append(f"    {my_id} --> {child_start}")
            lines.append(f"    {child_end} --> {my_id}")
            # We exit from the true path of the Loop decision node
            exit_id = self._get_id()
            lines.append(f"    {exit_id}[ ]")  # Invisible stub to continue
            lines.append(f"    {my_id} -- Next --> {exit_id}")
            return my_id, exit_id

        if isinstance(node, AlternationNode):
            lines.append(f'    {my_id}{{ "OR" }}')
            l_s, l_e = self._build_node(node.left, lines)
            r_s, r_e = self._build_node(node.right, lines)

            join_id = self._get_id()
            lines.append(f"    {join_id}(( ))")  # Merge point

            lines.append(f"    {my_id} --> {l_s}")
            lines.append(f"    {my_id} --> {r_s}")
            lines.append(f"    {l_e} --> {join_id}")
            lines.append(f"    {r_e} --> {join_id}")
            return my_id, join_id

        if isinstance(node, GroupNode):
            # Draw subgraph
            _type = "Group"
            if getattr(node, "type", "") == "lookahead":
                _type = "Lookahead"
            elif getattr(node, "type", "") == "negative_lookahead":
                _type = "Neg-Lookahead"

            label = f'"{_type} {node.name if getattr(node, "name", None) else ""}"'

            lines.append(f"    subgraph {my_id} [{label}]")
            sub_start = "sub_start_" + my_id
            sub_end = "sub_end_" + my_id
            lines.append(f"        {sub_start}(( ))")
            lines.append(f"        {sub_end}(( ))")

            last = sub_start
            for child in node.children:
                c_s, c_e = self._build_node(child, lines)
                lines.append(f"        {last} --> {c_s}")
                last = c_e

            if not node.children:
                lines.append(f"        {last} --> {sub_end}")
            else:
                lines.append(f"        {last} --> {sub_end}")

            lines.append("    end")
            return sub_start, sub_end

        # Catch all
        name = type(node).__name__.replace("Node", "")
        lines.append(f'    {my_id}["[{name}]"]')
        return my_id, my_id
