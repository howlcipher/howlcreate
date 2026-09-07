"""Tests for semantic near-duplicate detection, clustering, and outlier identification."""

from howlcreate.engine.dedup import ConceptDeduplicator, compute_similarity
from howlcreate.models.idea import Idea


def test_similarity_near_duplicates():
    idea_1 = Idea(
        id="1",
        title="Decentralized Task Bounty Mesh",
        description="A peer-to-peer network where contributors claim bounties on automated test suites.",
        core_mechanism="Decentralized verification and payout via smart contracts.",
    )
    # Near duplicate with minor paraphrasing
    idea_2 = Idea(
        id="2",
        title="P2P Task Bounty Network",
        description="A peer network where remote contributors claim automated test task bounties.",
        core_mechanism="Decentralized escrow verification and payout via contracts.",
    )

    sim = compute_similarity(idea_1, idea_2)
    assert sim > 0.50, f"Expected high similarity, got {sim}"


def test_similarity_distinct_concepts():
    idea_1 = Idea(
        id="1",
        title="Decentralized Task Bounty Mesh",
        description="A peer-to-peer network where contributors claim bounties on automated test suites.",
        core_mechanism="Decentralized verification and payout via smart contracts.",
    )
    idea_distinct = Idea(
        id="3",
        title="Mycelial Nutrient Distribution Analogy",
        description="Fungal bio-mimicry for routing bandwidth across rural satellites.",
        core_mechanism="Biological capillary osmosis and fungal spore broadcasting.",
    )

    sim = compute_similarity(idea_1, idea_distinct)
    assert sim < 0.35, f"Expected low similarity, got {sim}"


def test_clustering_groups_duplicates_and_surfaces_outliers():
    idea_a1 = Idea(id="a1", title="Escrow Staking Mesh", description="Staking bounties on pull requests", core_mechanism="escrow")
    idea_a2 = Idea(id="a2", title="Escrow Bounty Staking Network", description="Bounties and staking on PRs", core_mechanism="escrow")
    idea_outlier = Idea(id="b1", title="Quantum Entangled Chrono-Scheduler", description="Temporal physics applied to queue theory", core_mechanism="exotic physics")

    dedup = ConceptDeduplicator(similarity_threshold=0.45)
    clusters, outliers = dedup.cluster_ideas([idea_a1, idea_a2, idea_outlier])

    assert len(clusters) >= 2
    # idea_a1 and idea_a2 should be in the same cluster
    assert idea_a1.cluster_id == idea_a2.cluster_id
    assert idea_outlier.cluster_id != idea_a1.cluster_id
    # Outlier should be recognized
    assert any(o.id == "b1" for o in outliers)
