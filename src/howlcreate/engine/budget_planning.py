"""Reserve synthesis and evaluated convergence without erasing unexplored nodes."""

from math import ceil


def downstream_reserve(pending_count: int, repair_attempts: int, synthesis: bool = True) -> int:
    # Reserve one possible repair for synthesis and each evaluation batch. Unknown
    # synthesis output size is handled by the explicitly bounded evaluation subset.
    attempts = 1 + repair_attempts
    return attempts * (int(synthesis) + max(1, ceil(pending_count / 8)))


def evaluation_subset(ideas: list, capacity: int, deduplicator) -> tuple[list, list[str]]:
    """Diverse bounded evaluation, never fabricated scores or erased candidates."""
    scored = [idea for idea in ideas if idea.evaluations]
    pending = [idea for idea in ideas if not idea.evaluations]
    if len(pending) <= capacity:
        return ideas, []
    clusters, _ = deduplicator.cluster_ideas(pending)
    # New synthesis appears last; choose newest per cluster, then round-robin
    # other members. Every unselected node remains in the graph as unevaluated.
    pools = [list(reversed(members)) for members in clusters.values()]
    selected = []
    while len(selected) < capacity and any(pools):
        for pool in pools:
            if pool and len(selected) < capacity:
                selected.append(pool.pop(0))
    ids = {idea.id for idea in selected}
    return scored + selected, [idea.id for idea in pending if idea.id not in ids]
