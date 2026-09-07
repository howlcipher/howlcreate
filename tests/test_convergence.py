"""Tests for multi-dimensional evaluation and diversity-preserving convergence."""

from howlcreate.engine.convergence import ConvergenceEngine
from howlcreate.models.idea import ConceptStatus, Idea


def test_convergence_diverse_selection(deterministic_provider):
    engine = ConvergenceEngine(top_n=2)

    # 3 ideas, two in cluster A, one in cluster B
    idea1 = Idea(id="c1-1", title="Bounty Staking Mesh", description="Bounties with staking", core_mechanism="staking")
    idea2 = Idea(id="c1-2", title="Bounty Staking Network", description="Bounties and staking on tasks", core_mechanism="staking")
    idea3 = Idea(id="c2-1", title="Mycelial Resource Swarm", description="Biological fungal routing", core_mechanism="spores")

    finalists, decisions = engine.converge([idea1, idea2, idea3], "Remote work problem", deterministic_provider)

    assert len(finalists) == 2
    finalist_ids = {f.id for f in finalists}
    assert "c2-1" in finalist_ids

    # Verify decision rationale exists for all ideas
    assert len(decisions) == 3
    for idea_id, dec in decisions.items():
        assert dec.status in ["FINALIST", "SET_ASIDE"]
        assert len(dec.rationale) > 0

    # Ensure finalists are marked FINALIST and non-finalists SET_ASIDE
    for f in finalists:
        assert f.status == ConceptStatus.FINALIST
