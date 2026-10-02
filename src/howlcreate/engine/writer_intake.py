"""Native HowlWriter intake: a copy package becomes a Create development.

HowlWriter emits ``howlwriter.copy_package/v1``. Create validates it
against the vendored schema, optionally binds it to the HowlDream
candidate it came from, and develops it into the shared
``howl.development_result/v1`` envelope with the copy in a typed,
schema-validated slot (``sandbox_prototype_design.writer_copy``) rather
than smuggled through assessment evidence. The shared envelope schema is
left unchanged; Dream/Writer/Create identities travel in ``lineage``.
"""

from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator

from howlcreate.engine.candidate_ingestion import (
    IngestionError,
    develop_candidate,
    scaffold_candidate,
    validate_dream_source,
)

WRITER_SCHEMA = "howlwriter.copy_package.v1"
USABLE_STATUS = "FACTUALLY_PRESERVED"


def validate_writer_package(package: Any) -> dict:
    if not isinstance(package, dict):
        raise IngestionError("Writer package must be a JSON object")
    schema = json.loads(
        files("howlcreate").joinpath("schemas", WRITER_SCHEMA + ".schema.json").read_text()
    )
    errors = sorted(Draft202012Validator(schema).iter_errors(package), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        where = "/".join(str(p) for p in first.absolute_path) or "(root)"
        raise IngestionError(f"Invalid {WRITER_SCHEMA} artifact at {where}: {first.message[:300]}")
    if package["authority"] != {"type": "ADVISORY", "executable": False}:
        raise IngestionError("Writer package requires advisory, non-executable authority")
    return deepcopy(package)


def writer_copy_slot(package: dict) -> dict:
    """The typed copy slot: usable proposals plus an honest list of withheld ones."""
    proposals = []
    for proposal in package["proposals"]:
        usable = proposal["factual_status"] == USABLE_STATUS
        proposals.append(
            {
                "item_id": proposal["item_id"],
                "proposal_item_id": proposal["proposal_item_id"],
                "desired_copy_role": proposal.get("desired_copy_role", ""),
                "current_text": proposal["current_text"],
                "proposed_text": proposal["proposed_text"],
                "factual_status": proposal["factual_status"],
                "origin": proposal["origin"],
                "evidence_refs": proposal["evidence_refs"],
                "usable": usable,
                # Withheld proposals fall back to the current copy at materialization.
                "materialized_text": proposal["proposed_text"]
                if usable
                else proposal["current_text"],
            }
        )
    return {
        "schema": WRITER_SCHEMA,
        "writer_proposal_id": package["writer_proposal_id"],
        "writer_request_id": package["request_id"],
        "factual_status": package["factual_status"],
        "source_idea_id": package["source_idea_id"],
        "source_run_id": package["source_run_id"],
        "source_component": package["source_component"],
        "source_component_role": package["source_component_role"],
        "writer_execution": {
            key: package["execution"].get(key)
            for key in ("actual_provider", "model", "remote", "inference_occurred", "path")
        },
        "proposals": proposals,
        "withheld_item_ids": [p["item_id"] for p in proposals if not p["usable"]],
    }


def _candidate_from_package(package: dict, dream: dict | None) -> dict:
    if dream is not None:
        candidate = deepcopy(dream)
    else:
        lines = [f"- {p['item_id']}: {p['proposed_text']}" for p in package["proposals"]]
        candidate = {
            "schema_version": "howl.candidate/v1",
            "candidate_id": package["source_idea_id"],
            "source_run_id": package["source_run_id"],
            "parent_request_id": package["request_id"],
            "objective": package.get("title") or "Materialize HowlWriter copy",
            "text": (
                "Writer copy package " + package["writer_proposal_id"] + "\n" + "\n".join(lines)
            )[:50000],
            "authority": {"type": "ADVISORY", "executable": False},
            "provenance": {
                "producer_component": package["source_component"],
                "observation_kind": "EXTERNALLY_OBSERVED",
                "transformations": ["writer_copy_package_intake"],
                "hard_constraints": package.get("factual_constraints", [])[:50],
            },
        }
    candidate.setdefault("provenance", {})["writer_package_ref"] = {
        "writer_proposal_id": package["writer_proposal_id"],
        "writer_request_id": package["request_id"],
    }
    return candidate


def develop_from_writer(
    package: Any,
    dream_candidate: Any = None,
    provider=None,
    *,
    max_calls: int = 32,
    scaffold: bool = False,
) -> dict:
    """Develop a Writer copy package (optionally bound to its Dream source)."""
    package = validate_writer_package(package)
    dream = None
    if dream_candidate is not None:
        dream = validate_dream_source(dream_candidate)
        if (dream["candidate_id"], dream["source_run_id"]) != (
            package["source_idea_id"],
            package["source_run_id"],
        ):
            raise IngestionError(
                "Writer package source_idea_id/source_run_id do not match the Dream candidate"
            )
    candidate = _candidate_from_package(package, dream)
    assessment = {
        "schema_version": "howl.assessment/v1",
        "assessment_id": "operator-selection-" + uuid4().hex,
        "candidate_id": candidate["candidate_id"],
        "disposition": "ACCEPT_FOR_DEVELOPMENT",
        "confidence": "UNKNOWN",
        "limitations": [
            (
                "Operator selected Writer copy for development; Writer fidelity is "
                "deterministic, not external verification"
            )
        ],
        "authority": {"type": "ADVISORY", "executable": False},
        "provenance": {
            "producer_component": "operator_selection",
            "observation_kind": "DETERMINISTIC",
        },
    }
    slot = writer_copy_slot(package)
    if scaffold:
        result = scaffold_candidate(candidate, assessment)
    else:
        if provider is None:
            raise IngestionError("develop requires an explicit model provider; use scaffold")
        result = develop_candidate(
            candidate, assessment, provider, max_calls=max_calls, writer_copy=slot
        )
    result["sandbox_prototype_design"]["writer_copy"] = slot
    result["lineage"].update(
        dream_source_id=package["source_idea_id"]
        if package["source_component"] == "howldream"
        else None,
        source_idea_id=package["source_idea_id"],
        source_run_id=package["source_run_id"],
        writer_request_id=package["request_id"],
        writer_proposal_id=package["writer_proposal_id"],
        create_development_id=result["development_id"],
    )
    result["provenance"]["contribution"] = {
        "component": "howlcreate",
        "operation": "DESIGNED",
        "inference_occurred": bool(
            result["provenance"].get("execution", {}).get("inference_occurred")
        ),
        "note": "Advisory design only; files exist only after `howlcreate materialize`.",
    }
    return result
