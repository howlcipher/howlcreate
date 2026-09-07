"""End-to-end integration tests for the creative reasoning pipeline."""

from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.formatting import export_howlframe_contract, export_howlplane_contract
from howlcreate.models.idea import ConceptStatus, EpistemicStatus
from howlcreate.providers.deterministic import DeterministicProvider


def test_full_pipeline_execution(temp_storage_dir):
    config = PipelineConfig(
        top_n=3,
        custom_storage_dir=temp_storage_dir,
        provider_name="deterministic",
    )
    pipeline = CreativePipeline(config=config)
    provider = DeterministicProvider()

    problem = "How could the Howl ecosystem create meaningful remote-work opportunities rather than merely being software about remote work?"
    record = pipeline.execute(problem, provider=provider)

    # 1. Run ID and timing
    assert record.run_id.startswith("run-")
    assert record.completed_at is not None

    # 2. Assumptions extracted & inverted
    assert len(record.assumptions) >= 1
    assert all(len(a.inversions) > 0 for a in record.assumptions)

    # 3. Reframings generated
    assert len(record.reframings) >= 1

    # 4. Divergent exploration: graph should contain multiple ideas across operators
    assert len(record.graph.nodes) >= 6
    assert record.graph.validate_dag() is True

    # 5. Convergence: finalists selected
    finalists = record.get_finalists()
    assert 1 <= len(finalists) <= 3
    for f in finalists:
        assert f.status == ConceptStatus.FINALIST
        assert f.composite_score() > 0.0

    # 6. Epistemic boundary preserved (speculations are not facts)
    for idea in record.graph.nodes.values():
        assert idea.epistemic_status in list(EpistemicStatus)
        assert isinstance(idea.speculations, list)

    # 7. Handoff export payloads
    plane_contract = export_howlplane_contract(record)
    assert plane_contract["source_system"] == "howlcreate"
    assert len(plane_contract["recommended_concepts"]) == len(finalists)

    frame_contract = export_howlframe_contract(record)
    assert frame_contract["source_system"] == "howlcreate"
    assert len(frame_contract["epistemic_invariants"]) == len(finalists)
