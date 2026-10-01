import json
from unittest.mock import patch

import pytest
from howl_provider_core import CallBudget, ProviderError

from howlcreate.cli.main import main
from howlcreate.engine.candidate_ingestion import (
    IngestionError,
    develop_candidate,
    scaffold_candidate,
)
from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.formatting.dream import export_dream_candidate
from howlcreate.providers.base import BaseProvider, ProviderResponse
from howlcreate.providers.deterministic import DeterministicProvider
from howlcreate.providers.ollama import OllamaProvider
from howlcreate.providers.registry import ProviderRegistry
from howlcreate.providers.runtime import FallbackProvider, TrackedProvider
from test_candidate_ingestion import make_payloads


def test_auto_never_discovers_local(monkeypatch):
    monkeypatch.setenv("HOWL_FORBID_LOCAL_INFERENCE", "1")
    with patch.object(OllamaProvider, "is_available", side_effect=AssertionError("no discovery")):
        registry = ProviderRegistry()
        assert isinstance(registry.get_provider("auto"), DeterministicProvider)
        with pytest.raises(ProviderError):
            registry.get_provider("ollama", allow_local=True)
        with pytest.raises(ProviderError):
            registry.get_provider("nonexistent-provider")


def test_local_endpoint_overrides_rejected(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
    with pytest.raises(ProviderError):
        ProviderRegistry().get_provider("openai")


def test_cached_local_provider_rejected(monkeypatch):
    registry = ProviderRegistry()
    registry.register("cached", OllamaProvider())
    monkeypatch.setenv("HOWL_FORBID_LOCAL_INFERENCE", "1")
    with pytest.raises(ProviderError):
        registry.get_provider("cached", allow_local=True)


@pytest.mark.parametrize("limit", [0, 1, 13, 14])
def test_budget_preserves_partial(tmp_path, limit):
    provider = DeterministicProvider()
    result = CreativePipeline(PipelineConfig(max_calls=limit, custom_storage_dir=tmp_path)).execute(
        "Design a streaming parser", provider
    )
    assert result.metadata["call_count"] == limit
    assert len(provider.call_history) == limit
    assert result.metadata["stop_reason"] == "BUDGET_EXHAUSTED"
    assert result.metadata["status"] == "PARTIAL"
    assert list(tmp_path.glob("*.json"))


def test_batching_and_fixture_dispatch():
    for objective in ["Design a streaming parser", "Design an adversarial streaming parser"]:
        provider = DeterministicProvider()
        result = CreativePipeline(PipelineConfig(save_run=False)).execute(objective, provider)
        assert len(result.assumptions) == 2
        assert result.metadata["call_count"] == 15
        assert sum(x["operation"] == "evaluation_batch" for x in provider.call_history) == 2
        assert len(result.graph.nodes) == 15
        assert all(x["inference_occurred"] is False for x in result.metadata["executions"])
        assert all(x["mocked"] for x in result.metadata["executions"])
        assert not any("escrow" in idea.description for idea in result.graph.nodes.values())


def test_schema_identity_and_provenance():
    candidate, assessment = make_payloads()
    assessment["candidate_id"] = "other"
    with pytest.raises(IngestionError, match="does not match"):
        scaffold_candidate(candidate, assessment)
    assessment["candidate_id"] = candidate["candidate_id"]
    result = scaffold_candidate(candidate, assessment)
    assert result["provenance"]["source_candidate"]["claims"] == candidate["claims"]
    assert result["provenance"]["source_assessment"] == assessment
    assert "HowlFrame" not in result["architecture_proposal"]
    assert "operator" in result["architecture_proposal"]
    assert result["provenance"]["execution"]["inference_occurred"] is False
    with pytest.warns(DeprecationWarning):
        develop_candidate(candidate, assessment)
    candidate["authority"] = "NONE"
    with pytest.raises(IngestionError, match="typed advisory authority"):
        scaffold_candidate(candidate, assessment)


class FakeRemote(BaseProvider):
    def generate(self, prompt, **kwargs):
        data = {
            "sandbox_prototype_design": {"mechanism": "bounded streaming parsing"},
            "test_specification": [{"assertion": "handles incomplete utf8"}],
            "architecture_proposal": "Candidate-specific bounded parser",
        }
        return ProviderResponse(
            json.dumps(data),
            "fake-model",
            "fake_remote",
            metadata={"execution": {"actual_provider": "fake_remote", "mocked": True}},
        )


def test_develop_rejects_mock_and_consumes_candidate():
    candidate, assessment = make_payloads()
    with pytest.raises(IngestionError, match="Model-backed"):
        develop_candidate(candidate, assessment, FakeRemote())

    class ObservedFake(FakeRemote):
        def generate(self, prompt, **kwargs):
            assert candidate["text"] in prompt
            response = super().generate(prompt, **kwargs)
            # Simulates a live adapter response; the test itself remains a mock.
            response.metadata["execution"]["mocked"] = False
            return response

    result = develop_candidate(candidate, assessment, ObservedFake())
    assert result["provenance"]["source_candidate"] == candidate
    assert result["provenance"]["call_count"] == 1
    assert result["test_specification"][0]["status"] == "PROPOSED_NOT_EXECUTED"
    assert "bounded streaming parsing" in str(result["sandbox_prototype_design"])


def test_export_retains_identity():
    provider = DeterministicProvider()
    record = CreativePipeline(PipelineConfig(save_run=False)).execute(
        "Design a text parser", provider
    )
    idea = record.get_finalists()[0]
    candidate = export_dream_candidate(record, idea.id)
    assert candidate["candidate_id"] == idea.id
    assert candidate["provenance"]["source_idea"] == idea.to_dict()
    assert candidate["verified_constraints"] == []


def test_unknown_cli_and_zero_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))
    assert main(["explore", "test", "--provider", "misspelled"]) == 2
    assert main(["explore", "test", "--max-calls", "0", "--quiet"]) == 1


def test_fallback_budget_and_truth():
    class Failed(BaseProvider):
        def generate(self, prompt, **kwargs):
            raise ProviderError("remote failure")

    chain = FallbackProvider([Failed(), DeterministicProvider()], "remote-requested")
    budget = CallBudget(2)
    tracked = TrackedProvider(chain, budget, "remote-requested")
    response = tracked.generate_for("assumption_extraction", "test")
    assert budget.calls == 2
    execution = response.metadata["execution"]
    assert execution["actual_provider"] == "deterministic"
    assert execution["requested_provider"] == "remote-requested"
    assert execution["fallback_reason"]


def test_batch_partial_scores_preserved_without_fabrication():
    from howlcreate.engine.convergence import ConvergenceEngine
    from howlcreate.models.idea import Idea

    class Incomplete(DeterministicProvider):
        def generate_for(self, operation, prompt, **kwargs):
            response = super().generate_for(operation, prompt, **kwargs)
            if operation == "evaluation_batch":
                values = response.structured_data["evaluations"]
                del values["missing"]
            return response

    first = Idea("valid", "Valid", "Inspect buffer boundaries")
    second = Idea("missing", "Missing", "Inspect encoding boundaries")
    with pytest.raises(ValueError, match="incomplete batch evaluation"):
        ConvergenceEngine().converge([first, second], "Parse text", Incomplete())
    assert len(first.evaluations) == 1
    assert second.evaluations == []


def test_duplicate_json_keys_rejected():
    response = ProviderResponse('{"evaluations":{"c":{},"c":{}}}', "unknown", "fake")
    with pytest.raises(ProviderError, match="duplicate"):
        response.extract_json()


def test_optional_ecosystem_weight():
    from howlcreate.engine.convergence import ConvergenceEngine

    default = ConvergenceEngine()
    assert "ecosystem_fit" not in default.dimensions
    explicit = ConvergenceEngine(ecosystem_fit_weight=0.1)
    assert explicit.weights["ecosystem_fit"] == 0.1
    assert sum(explicit.weights.values()) == pytest.approx(1)
