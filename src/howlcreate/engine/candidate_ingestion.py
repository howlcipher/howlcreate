"""Validated, advisory candidate scaffolding and model-backed development."""

import json
import warnings
from copy import deepcopy
from datetime import datetime, timezone
from importlib.resources import files
from typing import Any, Dict
from uuid import uuid4

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from howl_provider_core import CallBudget, ProviderError
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.providers.runtime import TrackedProvider


class IngestionError(ValueError):
    """A malformed, mismatched or unauthorized artifact was rejected."""


def validate_envelope(value: dict, name: str):
    schema = json.loads(files("howlcreate").joinpath("schemas", name + ".schema.json").read_text())
    try:
        Draft202012Validator(schema).validate(value)
    except ValidationError as error:
        raise IngestionError(
            f"Invalid {name} artifact; check schema and advisory authority"
        ) from error


def _inputs(candidate, assessment):
    for value in (candidate, assessment):
        if not isinstance(value, dict) or not isinstance(value.get("authority"), dict):
            raise IngestionError("Missing typed advisory authority; legacy handoffs require export")
        if value["authority"] != {"type": "ADVISORY", "executable": False}:
            raise IngestionError("Authority escalation prohibited: advisory authority required")
    validate_envelope(candidate, "howl.candidate.v1")
    validate_envelope(assessment, "howl.assessment.v1")
    if candidate["candidate_id"] != assessment["candidate_id"]:
        raise IngestionError("Assessment candidate_id does not match candidate")
    if assessment["disposition"] != "ACCEPT_FOR_DEVELOPMENT":
        raise IngestionError("Disposition must be 'ACCEPT_FOR_DEVELOPMENT'")
    return deepcopy(candidate), deepcopy(assessment)


def scaffold_candidate(candidate: Dict[str, Any], assessment: Dict[str, Any]) -> Dict[str, Any]:
    candidate, assessment = _inputs(candidate, assessment)
    identifier = candidate["candidate_id"]
    child_id = f"create-{uuid4().hex}"
    origin = candidate.get("provenance", {}).get("producer_component") or "unknown"
    assessor = assessment.get("provenance", {}).get("producer_component") or "unknown"
    idea = Idea(
        id=child_id,
        title=f"Scaffold for {identifier}",
        description=candidate["text"],
        problem_framing=candidate["objective"],
        parent_ids=[identifier],
        origin=origin,
        provenance={
            "producer_component": "howlcreate",
            "source_candidate": candidate,
            "source_assessment": assessment,
            "transformations": ["candidate_scaffold"],
        },
        operator_used="candidate_scaffold",
        assumptions=candidate.get("assumptions", []),
        constraints=candidate.get("verified_constraints", []),
        evidence_needs=candidate.get("unresolved_issues", []),
        epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
    )
    result = {
        "schema_version": "howl.development_result/v1",
        "development_id": f"dev-{uuid4().hex}",
        "source_candidate_id": identifier,
        "parent_request_id": candidate["parent_request_id"],
        "origin": origin,
        "epistemic_status": "IMAGINED_POSSIBILITY",
        "authority": {"type": "ADVISORY", "executable": False},
        "execution_authority": "NONE",
        "idea": idea.to_dict(),
        "lineage": {
            "parent_id": identifier,
            "child_id": child_id,
            "ancestors": [identifier],
            "source_lineage": candidate.get("provenance", {}).get("parent_ids", []),
        },
        "sandbox_prototype_design": {
            "target_sandbox_environment": "isolated_local_testbed (no inference or execution)",
            "implementation_steps": [
                f"Design a bounded prototype for: {candidate['text']}",
                "Validate declared assumptions before implementation",
            ],
            "isolation_controls": ["NO_PRODUCTION_DEPLOYMENT", "NO_IMPLICIT_NETWORK_EGRESS"],
        },
        "test_specification": [
            {
                "test_id": f"proposed-assumption-{i}",
                "assertion": assumption,
                "status": "PROPOSED_NOT_EXECUTED",
            }
            for i, assumption in enumerate(candidate.get("assumptions", []))
        ],
        "architecture_proposal": (
            f"# Candidate scaffold\n\nObjective: {candidate['objective']}\n\n"
            f"Proposal: {candidate['text']}\n\n"
            f"Assessment supplied by: {assessor}; identity is descriptive, not authenticated.\n\n"
            "NO EXECUTION OR DEPLOYMENT AUTHORITY. No model call or prototype execution occurred."
        ),
        "provenance": {
            "producer_component": "howlcreate",
            "observation_kind": "DETERMINISTIC",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "transformations": ["candidate_scaffold"],
            "development_method": "SCAFFOLD",
            "source_candidate": candidate,
            "source_assessment": assessment,
            "execution": {"deterministic": True, "mocked": False, "inference_occurred": False},
        },
    }
    validate_envelope(result, "howl.development_result.v1")
    return result


def develop_candidate(candidate, assessment, provider=None, *, max_calls=32):
    """Legacy two-argument usage is a deprecated scaffold, never model-backed development."""
    if provider is None:
        warnings.warn(
            "develop_candidate without provider is deprecated; use scaffold_candidate",
            DeprecationWarning,
            stacklevel=2,
        )
        return scaffold_candidate(candidate, assessment)
    result = scaffold_candidate(candidate, assessment)
    tracked = TrackedProvider(
        provider,
        CallBudget(max_calls),
        getattr(provider, "requested_provider", type(provider).__name__),
    )
    prompt = (
        "Develop this supplied candidate into a candidate-specific advisory design and proposed "
        "tests. Preserve uncertainty; source assertions are not verified by your output. "
        "Return JSON with sandbox_prototype_design (object), test_specification (array of objects), "
        "and architecture_proposal (string). Do not execute tools, code or tests.\n"
        + json.dumps({"candidate": candidate, "assessment": assessment})
    )
    response = tracked.generate_for("candidate_development", prompt, json_mode=True)
    execution = response.metadata["execution"]
    if execution.get("deterministic") or execution.get("mocked"):
        raise IngestionError(
            "Model-backed develop requires a model provider; use scaffold for fixtures"
        )
    data = response.extract_json()
    if not isinstance(data, dict) or not isinstance(data.get("sandbox_prototype_design"), dict):
        raise ProviderError("Malformed candidate development design")
    if (
        not isinstance(data.get("test_specification"), list)
        or not all(isinstance(item, dict) for item in data["test_specification"])
        or not isinstance(data.get("architecture_proposal"), str)
    ):
        raise ProviderError("Malformed proposed tests or architecture")
    result.update(
        {
            key: data[key]
            for key in ("sandbox_prototype_design", "test_specification", "architecture_proposal")
        }
    )
    result["sandbox_prototype_design"]["isolation_controls"] = [
        "NO_EXECUTION",
        "NO_PRODUCTION_DEPLOYMENT",
        "NO_IMPLICIT_NETWORK_EGRESS",
    ]
    for test in result["test_specification"]:
        test["status"] = "PROPOSED_NOT_EXECUTED"
        test.pop("actual_outcome", None)
    result["architecture_proposal"] += "\n\nNO EXECUTION OR DEPLOYMENT AUTHORITY."
    result["provenance"].update(
        development_method="MODEL_BACKED",
        observation_kind="EXTERNALLY_OBSERVED",
        transformations=["candidate_development"],
        execution=execution,
        call_count=tracked.budget.calls,
    )
    validate_envelope(result, "howl.development_result.v1")
    return result
