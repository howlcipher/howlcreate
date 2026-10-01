"""Typed Create-to-Dream candidate conversion preserving source identities."""

from howlcreate.engine.candidate_ingestion import validate_envelope
from howlcreate.models.run import RunRecord


def export_dream_candidate(record: RunRecord, candidate_id: str):
    if candidate_id not in record.graph.nodes:
        raise ValueError("candidate ID not present in run")
    idea = record.graph.nodes[candidate_id]
    source = idea.to_dict()

    claims = [
        {
            "id": f"{idea.id}/claim/mechanism",
            "candidate_id": idea.id,
            "kind": (
                idea.epistemic_status.value
                if idea.epistemic_status
                else "HYPOTHESIS"
            ),
            "text": f"{idea.title}: {idea.core_mechanism or idea.description}",
            "status": "UNVERIFIED",
            "epistemic_status": (
                idea.epistemic_status.value
                if idea.epistemic_status
                else "HYPOTHESIS"
            ),
            "extractor": "howlcreate_export/v1",
            "confidence": "ADVISORY",
            "evidence_needs": list(idea.evidence_needs),
        }
    ]
    for idx, asm in enumerate(idea.assumptions):
        claims.append(
            {
                "id": f"{idea.id}/claim/assumption/{idx + 1}",
                "candidate_id": idea.id,
                "kind": "ASSUMPTION",
                "text": asm,
                "status": "UNVERIFIED",
                "epistemic_status": "ASSUMPTION",
                "extractor": "howlcreate_export/v1",
            }
        )
    for idx, spec in enumerate(idea.speculations):
        claims.append(
            {
                "id": f"{idea.id}/claim/speculation/{idx + 1}",
                "candidate_id": idea.id,
                "kind": "SPECULATION",
                "text": spec,
                "status": "UNVERIFIED",
                "epistemic_status": "SPECULATION",
                "extractor": "howlcreate_export/v1",
            }
        )

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
        "claims": claims,
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
            "source_run_id": record.run_id,
            "source_run_path": record.metadata.get("storage_path"),
            "parent_lineage": [
                {"id": pid, "title": record.graph.nodes[pid].title}
                for pid in idea.parent_ids
                if pid in record.graph.nodes
            ],
            "observation_kind": (
                "DETERMINISTIC"
                if (idea.provenance.get("execution") or {}).get("deterministic")
                else "EXTERNALLY_OBSERVED"
            ),
        },
    }
    validate_envelope(value, "howl.candidate.v1")
    return value
