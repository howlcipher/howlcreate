"""Tests verifying behavior of all individual creative operators."""

from howlcreate.models.idea import ConceptStatus
from howlcreate.operators.adversarial import AdversarialCritiqueOperator
from howlcreate.operators.analogy import AnalogicalReasoningOperator
from howlcreate.operators.assumptions import AssumptionOperator
from howlcreate.operators.branching import IndependentBranchingOperator
from howlcreate.operators.combination import ForcedCombinationOperator
from howlcreate.operators.constraints import ConstraintMutationOperator
from howlcreate.operators.extremes import ExtremeSolutionsOperator
from howlcreate.operators.reframing import ReframingOperator
from howlcreate.operators.second_order import SecondOrderOperator
from howlcreate.operators.simplification import SimplificationOperator
from howlcreate.operators.substitution import SubstitutionOperator
from howlcreate.operators.synthesis import SynthesisOperator


def test_assumption_operator(deterministic_provider):
    op = AssumptionOperator()
    res = op.execute("How to enable remote work without managers?", deterministic_provider)

    assert len(res.assumptions) >= 1
    assert any(len(a.inversions) > 0 for a in res.assumptions)
    assert len(res.ideas) >= 1


def test_reframing_operator(deterministic_provider):
    op = ReframingOperator()
    res = op.execute("How to reduce cloud compute bills?", deterministic_provider)

    assert len(res.reframings) >= 1
    assert len(res.ideas) >= 1
    for idea in res.ideas:
        assert idea.origin.startswith("reframe:")


def test_independent_branching_operator(deterministic_provider):
    op = IndependentBranchingOperator(branch_archetype="Cryptographer")
    res = op.execute("Build an offline communication mesh", deterministic_provider)

    assert len(res.ideas) >= 1
    assert res.metadata["archetype"] == "Cryptographer"


def test_constraint_mutation_operator(deterministic_provider, sample_idea_a):
    op = ConstraintMutationOperator()
    res = op.execute("Software deployment pipeline", deterministic_provider, context_ideas=[sample_idea_a])

    assert len(res.ideas) >= 1
    for idea in res.ideas:
        assert len(idea.constraints) > 0


def test_analogical_reasoning_operator(deterministic_provider):
    op = AnalogicalReasoningOperator()
    res = op.execute("Distributed consensus in unreliable networks", deterministic_provider)

    assert len(res.ideas) >= 1
    assert any(len(idea.analogies) > 0 for idea in res.ideas)


def test_forced_combination_operator(deterministic_provider, sample_idea_a, sample_idea_b):
    op = ForcedCombinationOperator()
    res = op.execute(
        "Remote work opportunities",
        deterministic_provider,
        context_ideas=[sample_idea_a, sample_idea_b]
    )

    assert len(res.ideas) >= 1
    hybrid = res.ideas[0]
    assert sample_idea_a.id in hybrid.parent_ids
    assert sample_idea_b.id in hybrid.parent_ids
    assert hybrid.status == ConceptStatus.COMBINED


def test_adversarial_critique_operator(deterministic_provider, sample_idea_a):
    op = AdversarialCritiqueOperator()
    res = op.execute(
        "Remote work opportunities",
        deterministic_provider,
        context_ideas=[sample_idea_a]
    )

    # Check that original idea has recorded criticisms
    assert len(sample_idea_a.criticisms) > 0
    assert sample_idea_a.status == ConceptStatus.CHALLENGED

    # Check that hardened mutation was spawned
    assert len(res.ideas) >= 1
    hardened = res.ideas[0]
    assert sample_idea_a.id in hardened.parent_ids
    assert hardened.status == ConceptStatus.MUTATED


def test_second_order_operator(deterministic_provider, sample_idea_a):
    op = SecondOrderOperator()
    res = op.execute("Remote work", deterministic_provider, context_ideas=[sample_idea_a])
    assert len(res.ideas) >= 1


def test_extreme_solutions_operator(deterministic_provider):
    op = ExtremeSolutionsOperator()
    res = op.execute("Database latency", deterministic_provider)
    assert len(res.ideas) >= 1


def test_simplification_operator(deterministic_provider):
    op = SimplificationOperator()
    res = op.execute("Complex regulatory compliance", deterministic_provider)
    assert len(res.ideas) >= 1


def test_substitution_operator(deterministic_provider):
    op = SubstitutionOperator()
    res = op.execute("Centralized platform fee", deterministic_provider)
    assert len(res.ideas) >= 1


def test_synthesis_operator(deterministic_provider, sample_idea_a, sample_idea_b):
    op = SynthesisOperator()
    res = op.execute(
        "Unified architecture",
        deterministic_provider,
        context_ideas=[sample_idea_a, sample_idea_b]
    )
    assert len(res.ideas) >= 1
    synth = res.ideas[0]
    assert synth.status == ConceptStatus.COMBINED
