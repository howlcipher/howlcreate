"""Tests for core data models and epistemic status preservation."""

from howlcreate.models.idea import (
    ConceptEvaluation,
    EpistemicStatus,
    Idea,
    ScoreDetail,
)
from howlcreate.models.operator import AssumptionItem, ReframingLens
from howlcreate.models.run import ConvergenceDecision, RunRecord


def test_idea_serialization_roundtrip():
    idea = Idea(
        id="idea-123",
        title="Decentralized Task Registry",
        description="A distributed registry for verifiable tasks.",
        core_mechanism="Merkle DAG proofs",
        epistemic_status=EpistemicStatus.HYPOTHESIS,
        assumptions=["Network nodes are semi-reliable"],
        speculations=["Adoption will exceed 500 guilds in year one"],
        evidence_needs=["Latency benchmarks over P2P transport"],
    )

    data = idea.to_dict()
    assert data["id"] == "idea-123"
    assert data["epistemic_status"] == "HYPOTHESIS"
    assert len(data["assumptions"]) == 1
    assert len(data["speculations"]) == 1

    restored = Idea.from_dict(data)
    assert restored.id == idea.id
    assert restored.title == idea.title
    assert restored.epistemic_status == EpistemicStatus.HYPOTHESIS
    assert restored.speculations == idea.speculations


def test_epistemic_boundary_distinction():
    # Verify that speculation is distinguished from facts and hypotheses
    assert EpistemicStatus.SPECULATION != EpistemicStatus.FACT
    assert EpistemicStatus.HYPOTHESIS != EpistemicStatus.FACT
    assert EpistemicStatus.IMAGINED_POSSIBILITY != EpistemicStatus.FACT


def test_concept_evaluation_composite():
    scores = {
        "novelty": ScoreDetail("novelty", 0.8, "Highly distinct", 0.1),
        "feasibility": ScoreDetail("feasibility", 0.6, "Feasible with effort", 0.2),
    }
    evaluation = ConceptEvaluation(
        evaluator_id="critic_01",
        scores=scores,
        composite_score=0.7,
        strengths=["Clear boundary"],
        weaknesses=["Requires initial liquidity"],
    )

    data = evaluation.to_dict()
    restored = ConceptEvaluation.from_dict(data)
    assert restored.composite_score == 0.7
    assert restored.scores["novelty"].score == 0.8
    assert restored.scores["novelty"].uncertainty == 0.1


def test_run_record_serialization_roundtrip():
    record = RunRecord(
        run_id="run-test-xyz",
        problem="How to coordinate distributed work asynchronously?",
        assumptions=[
            AssumptionItem("asm-1", "Workers require synchronous meetings", True, ["No meetings ever"])
        ],
        reframings=[
            ReframingLens("lens-1", "Adversary", "How to extract value maliciously?", "Security")
        ],
        finalist_ids=["idea-1"],
        decisions={
            "idea-1": ConvergenceDecision("idea-1", "FINALIST", "Superior architecture")
        },
    )

    data = record.to_dict()
    assert data["run_id"] == "run-test-xyz"
    assert len(data["assumptions"]) == 1
    assert len(data["reframings"]) == 1
    assert data["finalist_ids"] == ["idea-1"]

    restored = RunRecord.from_dict(data)
    assert restored.run_id == record.run_id
    assert restored.assumptions[0].statement == "Workers require synchronous meetings"
    assert restored.decisions["idea-1"].status == "FINALIST"
