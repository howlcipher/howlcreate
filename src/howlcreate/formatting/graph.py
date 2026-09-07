"""Visual and text lineage graph representations."""

from __future__ import annotations

from typing import List
from howlcreate.models.idea import ConceptStatus, LineageGraph


def to_mermaid(graph: LineageGraph) -> str:
    """Render the concept lineage DAG as a Mermaid diagram."""
    lines: List[str] = ["```mermaid", "graph TD"]

    # Render nodes with styling
    for node_id, idea in graph.nodes.items():
        title_sanitized = idea.title.replace('"', "'")
        score = f" [{idea.composite_score():.2f}]" if idea.evaluations else ""
        if idea.status == ConceptStatus.FINALIST:
            lines.append(f'    {node_id}["★ {title_sanitized}{score}"]:::finalist')
        elif idea.status == ConceptStatus.COMBINED:
            lines.append(f'    {node_id}["⚯ {title_sanitized}{score}"]:::combined')
        elif idea.status == ConceptStatus.MUTATED:
            lines.append(f'    {node_id}["⚡ {title_sanitized}{score}"]:::mutated')
        else:
            lines.append(f'    {node_id}["{title_sanitized}{score}"]')

    # Render edges
    for edge in graph.edges:
        op_label = edge.operator.replace("_", " ")
        lines.append(f'    {edge.parent_id} -->|"{op_label}"| {edge.child_id}')

    # Class definitions
    lines.append("    classDef finalist fill:#1e3a8a,stroke:#3b82f6,stroke-width:3px,color:#fff;")
    lines.append("    classDef combined fill:#581c87,stroke:#a855f7,stroke-width:2px,color:#fff;")
    lines.append("    classDef mutated fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#fff;")
    lines.append("```")

    return "\n".join(lines)


def to_ascii_tree(graph: LineageGraph) -> str:
    """Render an ASCII lineage view of concept evolution."""
    lines: List[str] = []

    # Find roots (nodes with no parents)
    child_ids = {e.child_id for e in graph.edges}
    roots = [node_id for node_id in graph.nodes if node_id not in child_ids]

    # Map children
    children_map: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in graph.nodes}
    for edge in graph.edges:
        if edge.parent_id in children_map:
            children_map[edge.parent_id].append((edge.child_id, edge.operator))

    def _render_branch(curr_id: str, prefix: str = "", is_last: bool = True):
        node = graph.nodes.get(curr_id)
        if not node:
            return
        star = "★ " if node.status == ConceptStatus.FINALIST else ""
        lines.append(f"{prefix}{'└── ' if is_last else '├── '}{star}[{node.id}] {node.title} ({node.operator_used})")

        kids = children_map.get(curr_id, [])
        for i, (kid_id, op) in enumerate(kids):
            next_prefix = prefix + ("    " if is_last else "│   ")
            _render_branch(kid_id, next_prefix, i == len(kids) - 1)

    for i, root in enumerate(roots):
        node = graph.nodes[root]
        star = "★ " if node.status == ConceptStatus.FINALIST else ""
        lines.append(f"{star}[{node.id}] {node.title} ({node.operator_used})")
        kids = children_map.get(root, [])
        for j, (kid_id, op) in enumerate(kids):
            _render_branch(kid_id, " ", j == len(kids) - 1)

    return "\n".join(lines)
