"""Typed Create-to-Dream candidate conversion preserving source identities."""

from howlcreate.engine.candidate_ingestion import validate_envelope
from howlcreate.models.run import RunRecord


def export_dream_candidate(record: RunRecord, candidate_id: str):
    if candidate_id not in record.graph.nodes:
        raise ValueError("candidate ID not present in run")
    idea = record.graph.nodes[candidate_id]
    source = idea.to_dict()
    value = {
        "schema_version": "howl.candidate/v1",
        "candidate_id": idea.id,
        "source_run_id": record.run_id,
        "parent_request_id": record.run_id,
        "objective": record.problem,
        "text": idea.description + "\n" + idea.core_mechanism,
        "condition": "create",
        "trust": "UNVERIFIED",
        "status": "GENERATED",
        "authority": {"type": "ADVISORY", "executable": False},
        "claims": [],
        "evidence_refs": [],
        "assumptions": list(idea.assumptions),
        "unresolved_issues": list(idea.evidence_needs + idea.unanswered_questions),
        "contradictions": [],
        "verified_constraints": [],
        "provenance": {
            "producer_component": "howlcreate",
            "created_at": idea.created_at,
            "transformations": ["create_candidate_export"],
            "source_idea": source,
            "parent_ids": list(idea.parent_ids),
            "execution": idea.provenance.get("execution"),
            "source_graph": record.graph.to_dict(),
            "observation_kind": "DETERMINISTIC"
            if (idea.provenance.get("execution") or {}).get("deterministic")
            else "EXTERNALLY_OBSERVED",
        },
    }
    validate_envelope(value, "howl.candidate.v1")
    return value
