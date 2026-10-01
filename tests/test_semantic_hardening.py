"""Tests for semantic completion validation, hard constraints, and structured export."""

import json
from howlcreate.engine.convergence import ConvergenceEngine
from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.formatting.dream import export_dream_candidate
from howlcreate.models.idea import ConceptStatus, Idea
from howlcreate.models.run import RunRecord
from howlcreate.providers.base import BaseProvider, ProviderResponse
from howlcreate.providers.deterministic import DeterministicProvider


class EmptyProvider(BaseProvider):
    def __init__(self):
        super().__init__(model_name="mock-empty")

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ProviderResponse:
        return ProviderResponse(
            content="{}",
            model=self.model_name,
            provider="mock-empty",
            structured_data={},
        )


def test_empty_provider_output_yields_invalid_provider_output(tmp_path):
    config = PipelineConfig(
        top_n=3,
        custom_storage_dir=tmp_path,
        provider_name="mock-empty",
    )
    pipeline = CreativePipeline(config=config)
    provider = EmptyProvider()

    record = pipeline.execute("Solve distributed consensus without clocks", provider=provider)

    assert record.metadata.get("status") == "INVALID_PROVIDER_OUTPUT"
    assert record.metadata.get("stop_reason") == "ZERO_CONCEPTS_GENERATED"
    assert len(record.finalist_ids) == 0


def test_hard_constraint_gating_disqualifies_high_novelty_violator():
    engine = ConvergenceEngine(
        top_n=1,
        hard_constraints=["Zero wall-clock reliance"],
    )
    provider = DeterministicProvider()

    # Idea 1 has high novelty/appeal but violates the hard constraint
    violating_idea = Idea(
        id="c1",
        title="NTP Timestamp Oracle",
        description="Synchronize across nodes using high-precision wall clock and NTP time servers",
        core_mechanism="wall clock sync via NTP",
    )
    # Idea 2 complies with the hard constraint
    compliant_idea = Idea(
        id="c2",
        title="Monotonic Epoch Counter",
        description=(
            "Use logical epoch counters and Lamport generation increments with no wall clock"
        ),
        core_mechanism="logical epochs and Lamport increments",
    )

    finalists, decisions = engine.converge(
        [violating_idea, compliant_idea],
        "Design distributed lease coordination",
        provider,
        hard_constraints=["Zero wall-clock reliance"],
    )

    assert len(finalists) == 1
    assert finalists[0].id == "c2"
    assert finalists[0].status == ConceptStatus.FINALIST

    # Verify violating idea was set aside with explicit constraint violation rationale
    assert violating_idea.id in decisions
    dec = decisions[violating_idea.id]
    assert dec.status == ConceptStatus.SET_ASIDE.value
    assert "Disqualified by hard constraint violation" in dec.rationale
    assert any("wall-clock" in r.lower() or "wall clock" in r.lower() for r in dec.risks_noted)
    assert violating_idea.status == ConceptStatus.SET_ASIDE


def test_no_viable_candidates_when_all_violate_constraints(tmp_path):
    config = PipelineConfig(
        top_n=2,
        custom_storage_dir=tmp_path,
        provider_name="deterministic",
        hard_constraints=["Requires quantum entanglement teleporter"],
    )
    pipeline = CreativePipeline(config=config)
    provider = DeterministicProvider()

    record = pipeline.execute("Any problem statement", provider=provider)

    assert record.metadata.get("status") == "NO_VIABLE_CANDIDATES"
    assert record.metadata.get("stop_reason") == "NO_VIABLE_CANDIDATES"
    assert len(record.finalist_ids) == 0


def test_structured_candidate_export_and_slim_handoff():
    record = RunRecord(
        run_id="run-test-slim-01",
        problem="Epoch-based lease coordination",
        metadata={"storage_path": "/tmp/runs/run-test-slim-01.json"},
    )
    idea = Idea(
        id="cand-001",
        title="Monotonic Lease Barrier",
        description="Fencing tokens and monotonic generation counters for lease renewal",
        core_mechanism="fencing tokens with monotonic generation verification",
        assumptions=["Storage layer supports atomic compare-and-swap"],
        speculations=["May reduce network chatter under partition recovery"],
        evidence_needs=["Measure CAS latency under 100 concurrent nodes"],
    )
    record.graph.add_idea(idea)
    record.finalist_ids = [idea.id]

    payload = export_dream_candidate(record, "cand-001")

    # 1. Structure assertions
    assert payload["schema_version"] == "howl.candidate/v1"
    assert payload["candidate_id"] == "cand-001"
    assert len(payload["claims"]) == 3  # mechanism, assumption, speculation

    mechanism_claim = payload["claims"][0]
    assert mechanism_claim["id"] == "cand-001/claim/mechanism"
    assert mechanism_claim["evidence_needs"] == ["Measure CAS latency under 100 concurrent nodes"]

    asm_claim = payload["claims"][1]
    assert asm_claim["kind"] == "ASSUMPTION"
    assert asm_claim["text"] == "Storage layer supports atomic compare-and-swap"

    spec_claim = payload["claims"][2]
    assert spec_claim["kind"] == "SPECULATION"
    assert spec_claim["text"] == "May reduce network chatter under partition recovery"

    # 2. Reference-based slim payload assertion
    serialized = json.dumps(payload)
    payload_size_kb = len(serialized.encode("utf-8")) / 1024.0
    # Before: ~304 KB due to full embedded source_graph. Now: < 5 KB.
    assert payload_size_kb < 15.0, f"Payload size {payload_size_kb:.2f} KB exceeds 15 KB limit"
    assert "source_run_id" in payload["provenance"]
    assert "source_graph" not in payload["provenance"]


def test_cli_explore_with_hard_constraints(tmp_path, monkeypatch):
    from howlcreate.cli.main import main
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))
    output_file = tmp_path / "run.json"

    ret = main([
        "explore",
        "How to coordinate distributed jobs?",
        "--provider", "deterministic",
        "--hard-constraint", "Zero centralized single-point-of-failure",
        "--output", str(output_file),
    ])
    assert ret == 0
    assert output_file.exists()


def test_cli_explore_impossible_constraint_fails(tmp_path, monkeypatch):
    from howlcreate.cli.main import main
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))
    output_file = tmp_path / "run.json"

    ret = main([
        "explore",
        "How to coordinate distributed jobs?",
        "--provider", "deterministic",
        "--hard-constraint", "Requires quantum entanglement teleporter",
        "--output", str(output_file),
    ])
    # Fails closed because status is NO_VIABLE_CANDIDATES
    assert ret == 1
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["metadata"]["status"] == "NO_VIABLE_CANDIDATES"
