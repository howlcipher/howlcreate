"""Budget reservations and direct advisory Dream development without local inference."""

import json
import subprocess
import sys

import pytest

from howlcreate.engine.candidate_ingestion import IngestionError, develop_from_dream
from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.providers.deterministic import DeterministicProvider


def source():
    return {
        "schema_version": "howl.candidate/v1",
        "candidate_id": "dream-idea",
        "source_run_id": "dream-run",
        "parent_request_id": "request",
        "objective": "MLB team",
        "text": "IDEA: stadium accessibility routing",
        "trust": "UNVERIFIED",
        "status": "UNRESOLVED",
        "authority": {"type": "ADVISORY", "executable": False},
        "claims": [{"id": "claim", "kind": "HYPOTHESIS", "text": "Routing improves access"}],
        "evidence_refs": ["ledger"],
        "assumptions": ["route map exists"],
        "unresolved_issues": ["independent visitor wait measurement"],
        "provenance": {"producer_component": "howldream", "hard_constraints": ["No tracking"]},
    }


@pytest.mark.parametrize("limit", [8, 12, 32])
def test_reserved_synthesis_and_convergence(limit):
    provider = DeterministicProvider()
    result = CreativePipeline(PipelineConfig(max_calls=limit, save_run=False)).execute(
        "Developer platform opportunities", provider
    )
    assert result.metadata["status"] == "COMPLETE"
    assert "synthesis" in result.metadata["completed_phases"]
    assert "convergence" in result.metadata["completed_phases"]
    assert result.metadata["call_count"] <= limit
    assert result.finalist_ids
    assert all(idea.evaluations for idea in result.get_finalists())
    assert (
        result.metadata["advisory_dimension_leaders"]["highest_novelty"]["authority"] == "ADVISORY"
    )
    if limit < 32:
        assert result.metadata["completion_detail"] == "COMPLETE_REDUCED_PIPELINE"
        assert result.metadata["budget_plan"]["skipped_phases"]


def test_direct_dream_scaffold_preserves_entire_source():
    candidate = source()
    result = develop_from_dream(candidate, scaffold=True)
    assert result["source_candidate_id"] == "dream-idea"
    assert result["provenance"]["source_candidate"] == candidate
    assert result["idea"]["constraints"] == ["No tracking"]
    assert result["provenance"]["source_assessment"]["confidence"] == "UNKNOWN"
    assert result["execution_authority"] == "NONE"
    assert result["idea"]["evidence_needs"] == candidate["unresolved_issues"]


def test_dream_source_passed_into_creative_operators(tmp_path):
    provider = DeterministicProvider()
    result = CreativePipeline(PipelineConfig(max_calls=8, custom_storage_dir=tmp_path)).execute(
        "Develop selected opportunity", provider, source_candidate=source()
    )
    assert result.metadata["source_dream_candidate"] == source()
    assert result.config["hard_constraints"] == ["No tracking"]
    assert all("stadium accessibility routing" in row["prompt"] for row in provider.call_history)
    assert all("dream-idea" in row["prompt"] for row in provider.call_history)


@pytest.mark.parametrize(
    "update",
    [
        {"status": "REJECTED"},
        {"contradictions": ["critical"]},
        {"authority": {"type": "EXECUTE", "executable": True}},
    ],
)
def test_invalid_dream_source_cannot_bypass_gates(update):
    with pytest.raises(IngestionError):
        develop_from_dream({**source(), **update}, scaffold=True)


def test_direct_cli_scaffold(tmp_path):
    path = tmp_path / "dream.json"
    path.write_text(json.dumps(source()))
    process = subprocess.run(
        [sys.executable, "-m", "howlcreate.cli.main", "scaffold", "--from-dream", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["source_candidate_id"] == "dream-idea"


def test_budget_excess_output_preserves_deferred_nodes():
    from howlcreate.providers.base import ProviderResponse

    class ManyIdeas(DeterministicProvider):
        def generate_for(self, operation, prompt, **kwargs):
            response = super().generate_for(operation, prompt, **kwargs)
            if operation == "synthesis":
                payload = response.extract_json()
                payload["ideas"] = [
                    {
                        "title": f"Approach {i}",
                        "description": f"Mechanism for domain {i}",
                        "core_mechanism": f"Distinct workload {i}",
                    }
                    for i in range(24)
                ]
                return ProviderResponse(json.dumps(payload), response.model, response.provider)
            return response

    result = CreativePipeline(PipelineConfig(max_calls=8, save_run=False)).execute(
        "Developer platform", ManyIdeas()
    )
    assert result.finalist_ids
    assert result.metadata["budget_plan"]["deferred_evaluation_ids"]
    assert len(result.graph.nodes) > 8
    assert all(
        not result.graph.nodes[i].evaluations
        for i in result.metadata["budget_plan"]["deferred_evaluation_ids"]
    )
    assert result.metadata["call_count"] <= 8


def test_novelty_leader_survives_balanced_ranking_and_gates():
    from howlcreate.engine.convergence import ConvergenceEngine
    from howlcreate.models.idea import Idea

    provider = DeterministicProvider()
    engine = ConvergenceEngine(top_n=1)
    ideas = [
        Idea(id="conventional", title="standard", description="conventional"),
        Idea(id="creative", title="unusual", description="new mechanism"),
        Idea(id="forbidden", title="forbidden", description="violates: No tracking"),
    ]
    values = [(0.1, 0.9), (0.95, 0.5), (1.0, 1.0)]
    for idea, (novelty, other) in zip(ideas, values):
        engine.evaluate_idea(
            idea,
            "platform",
            provider,
            supplied_data={
                "scores": {
                    dim: {
                        "score": novelty if dim == "novelty" else other,
                        "uncertainty": 0.2,
                        "rationale": "authored fixture",
                    }
                    for dim in engine.dimensions
                },
            },
        )
    finalists, _ = engine.converge(ideas, "platform", provider, hard_constraints=["No tracking"])
    assert finalists[0].id == "conventional"
    assert engine.dimension_leaders["highest_novelty"]["candidate_id"] == "creative"
    assert all(row["candidate_id"] != "forbidden" for row in engine.dimension_leaders.values())


def test_dream_constraints_cannot_be_untyped_provenance():
    candidate = source()
    candidate["provenance"]["hard_constraints"] = "No tracking"
    with pytest.raises(IngestionError, match="hard_constraints"):
        develop_from_dream(candidate, scaffold=True)
