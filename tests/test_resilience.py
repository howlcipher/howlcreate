"""Failure injection at expensive state and accounting boundaries, without inference."""

import json
import pytest
from howl_provider_core import CallBudget, BudgetExceeded
from howlcreate.providers.base import BaseProvider, ProviderResponse
from howlcreate.providers.deterministic import DeterministicProvider
from howlcreate.providers.runtime import TrackedProvider
from howlcreate.engine.pipeline import CreativePipeline, PipelineConfig
from howlcreate.engine.storage import RunStorage


class Sequence(BaseProvider):
    def __init__(self, outputs):
        super().__init__("fixture")
        self.outputs = iter(outputs)
        self.prompts = []

    def generate(self, prompt, **kwargs):
        self.prompts.append(prompt)
        return ProviderResponse(
            next(self.outputs),
            "fixture",
            "fixture",
            metadata={
                "execution": {
                    "usage": {"input_tokens": 10},
                    "cost": 0.01,
                    "inference_occurred": True,
                    "model": "fixture",
                }
            },
        )


@pytest.mark.parametrize("malformed", ["{truncated", "not json", '{"ideas": ['])
def test_repair_success_preserves_usage(malformed):
    provider = Sequence([malformed, '{"ideas": []}'])
    tracked = TrackedProvider(provider, CallBudget(2), "fixture")
    response = tracked.generate_for("mutation", 'Return valid JSON: {"ideas": []}', json_mode=True)
    assert response.extract_json() == {"ideas": []}
    assert len(provider.prompts) == 2
    assert "EXPECTED_SCHEMA" in provider.prompts[1]
    assert "Do not regenerate" in provider.prompts[1]
    original, repaired = tracked.executions
    assert original["parse_status"] == "FAILED"
    assert original["raw_output"] == malformed
    assert original["usage"]["input_tokens"] == 10
    assert original["cost"] == 0.01
    assert original["repair_attempted"] is True
    assert repaired["repair_success"] is True
    assert repaired["response_kind"] == "REPAIRED_PROVIDER_RESPONSE"


def test_repair_failure_is_bounded_and_budgeted():
    provider = Sequence(["bad", "bad", '{"ideas": []}'])
    tracked = TrackedProvider(provider, CallBudget(2), "fixture")
    with pytest.raises(ValueError, match="malformed"):
        tracked.generate_for("mutation", "Return JSON", json_mode=True)
    assert len(provider.prompts) == 2
    assert all(e["parse_status"] == "FAILED" for e in tracked.executions)
    with pytest.raises(BudgetExceeded):
        tracked.generate_for("mutation", "Return JSON", json_mode=True)
    assert len(provider.prompts) == 2


class LaterFailure(DeterministicProvider):
    def generate_for(self, operation, prompt, **kwargs):
        if operation == "constraint_mutation":
            self.call_history.append({"operation": operation})
            return ProviderResponse("bad", "fixture", "fixture")
        return super().generate_for(operation, prompt, **kwargs)


def test_optional_failure_converges_surviving_graph(tmp_path):
    provider = LaterFailure()
    record = CreativePipeline(PipelineConfig(custom_storage_dir=tmp_path)).execute(
        "Design an accessible museum queue", provider
    )
    assert len(record.graph.nodes) >= 4
    assert record.finalist_ids
    assert record.metadata["status"] == "PARTIAL"
    assert record.metadata["completion_detail"] == "PARTIAL_WITH_FINALISTS"
    assert record.metadata["failed_phase"] == "mutation"
    failed = [e for e in record.metadata["executions"] if e["parse_status"] == "FAILED"]
    assert len(failed) == 2
    assert "mutation" not in record.metadata["completed_phases"]
    saved = RunStorage(tmp_path).load_run(record.run_id)
    assert saved.finalist_ids == record.finalist_ids


def test_interrupt_resume_preserves_ids_and_history(tmp_path):
    def interrupt(phase, payload):
        if phase == "phase" and payload["name"] == "mutation":
            raise KeyboardInterrupt()

    pipeline = CreativePipeline(
        PipelineConfig(custom_storage_dir=tmp_path, on_step_callback=interrupt)
    )
    provider = DeterministicProvider()
    with pytest.raises(KeyboardInterrupt):
        pipeline.execute("Museum queue", provider)
    path = next(tmp_path.glob("run-*.json"))
    before = json.loads(path.read_text())
    original_ids = set(before["graph"]["nodes"])
    prior_calls = before["metadata"]["call_count"]
    resumed_provider = DeterministicProvider()
    after = CreativePipeline(PipelineConfig(custom_storage_dir=tmp_path)).resume(
        str(path), resumed_provider
    )
    assert after.run_id == before["run_id"]
    assert original_ids <= set(after.graph.nodes)
    assert not any(
        c["operation"] in ("assumption_extraction", "reframing")
        for c in resumed_provider.call_history
    )
    assert after.metadata["executions"][:prior_calls] == before["metadata"]["executions"]
    assert after.metadata["call_count"] > prior_calls
    assert after.metadata["status"] == "COMPLETE"


def test_incompatible_resume_rejected(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"run_id": "old", "problem": "test"}))
    with pytest.raises(ValueError, match="incompatible"):
        CreativePipeline(PipelineConfig(custom_storage_dir=tmp_path)).resume(str(path))


def test_schema_failure_repaired_and_secret_redacted(monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "credential-value")
    provider = Sequence(['{"ideas": "credential-value"}', '{"ideas": []}'])
    tracked = TrackedProvider(provider, CallBudget(2), "fixture")
    tracked.generate_for("mutation", "Return JSON", json_mode=True)
    assert "credential-value" not in json.dumps(tracked.executions)


def test_partial_evaluation_preserves_evaluated_finalists(tmp_path):
    from howl_provider_core import ProviderError

    class FailedEvaluation(DeterministicProvider):
        def __init__(self):
            super().__init__()
            self.batches = 0

        def generate_for(self, operation, prompt, **kwargs):
            if operation == "evaluation_batch":
                self.batches += 1
                if self.batches == 2:
                    raise ProviderError("session limit reached")
            return super().generate_for(operation, prompt, **kwargs)

    record = CreativePipeline(PipelineConfig(custom_storage_dir=tmp_path)).execute(
        "Museum queue", FailedEvaluation()
    )
    assert record.metadata["status"] == "PARTIAL"
    assert record.finalist_ids
    assert all(record.graph.nodes[i].evaluations for i in record.finalist_ids)
    assert any(not idea.evaluations for idea in record.graph.nodes.values())


def test_duplicate_json_is_accounted_and_repaired():
    provider = Sequence(['{"ideas":[], "ideas":[]}', '{"ideas":[]}'])
    tracked = TrackedProvider(provider, CallBudget(2), "fixture")
    tracked.generate_for("mutation", "Return JSON", json_mode=True)
    assert len(tracked.executions) == 2
    assert tracked.executions[0]["usage"]["input_tokens"] == 10
    assert tracked.executions[-1]["repair_success"]


def test_http_parse_failure_retains_usage(monkeypatch):
    import io
    from howlcreate.providers.openai_compatible import OpenAICompatibleProvider
    from howl_provider_core import ProviderError

    provider = OpenAICompatibleProvider(api_base="https://provider.example/v1", api_key="fixture")
    payload = {
        "model": "observed-model",
        "usage": {"prompt_tokens": 11},
        "id": "request-1",
        "choices": [],
    }
    provider.opener.open = lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode())
    with pytest.raises(ProviderError) as error:
        provider.generate("fixture")
    assert error.value.execution["usage"]["prompt_tokens"] == 11
    assert error.value.execution["inference_occurred"] is True
    assert error.value.execution["parse_status"] == "FAILED"


def test_fallback_respects_disabled_repair():
    from howlcreate.providers.runtime import FallbackProvider

    source = Sequence(["bad", "bad"])
    chain = FallbackProvider([source, DeterministicProvider()], "fixture")
    tracked = TrackedProvider(chain, CallBudget(2), "fixture", repair_attempts=0)
    tracked.generate_for("assumption_extraction", "Return JSON", json_mode=True)
    assert len(source.prompts) == 1
    assert len(tracked.executions) == 2
    assert not tracked.executions[0]["repair_attempted"]
