"""Ecosystem export bridges for HowlPlane and HowlFrame."""

from __future__ import annotations

from typing import Any, Dict
from howlcreate.models.run import RunRecord


def export_howlplane_contract(record: RunRecord) -> Dict[str, Any]:
    """Generate a clean handoff payload for HowlPlane execution planning."""
    finalists = record.get_finalists()
    return {
        "source_system": "howlcreate",
        "run_id": record.run_id,
        "problem_statement": record.problem,
        "recommended_concepts": [
            {
                "concept_id": idea.id,
                "title": idea.title,
                "description": idea.description,
                "core_mechanism": idea.core_mechanism,
                "composite_score": idea.composite_score(),
                "assumptions": idea.assumptions,
                "constraints": idea.constraints,
                "suggested_plane_goal": f"Realize and implement prototype for {idea.title}",
            }
            for idea in finalists
        ],
    }


def export_howlframe_contract(record: RunRecord) -> Dict[str, Any]:
    """Generate an epistemic verification handoff payload for HowlFrame."""
    finalists = record.get_finalists()
    return {
        "source_system": "howlcreate",
        "run_id": record.run_id,
        "problem_statement": record.problem,
        "epistemic_invariants": [
            {
                "concept_id": idea.id,
                "title": idea.title,
                "explicit_assumptions": idea.assumptions,
                "speculative_assertions": idea.speculations,
                "required_evidence": idea.evidence_needs,
                "unanswered_questions": idea.unanswered_questions,
            }
            for idea in finalists
        ],
    }
