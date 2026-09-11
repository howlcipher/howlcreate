"""Candidate ingestion and deliberate sandbox development for HowlDream integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from howlcreate.models.idea import (
    ConceptStatus,
    EpistemicStatus,
    Idea,
    LineageGraph,
)


class IngestionError(Exception):
    """Raised when candidate ingestion or authority validation fails."""
    pass


def develop_candidate(
    candidate: Dict[str, Any],
    assessment: Dict[str, Any],
) -> Dict[str, Any]:
    """Ingest a HowlFrame-promoted candidate and produce a deliberate sandbox development plan.

    HowlCreate treats this as speculative exploration, not ground truth.
    It develops proposals in a sandbox; it does NOT deploy or mutate production.
    """
    # 1. Authority validation: fail closed on any execution attempt
    auth = candidate.get("authority", {})
    if auth.get("executable") is True or auth.get("type") != "ADVISORY":
        raise IngestionError(
            "Authority escalation prohibited: speculative candidate cannot claim execution authority"
        )

    assess_auth = assessment.get("authority", {})
    if assess_auth.get("executable") is True or assess_auth.get("type") != "ADVISORY":
        raise IngestionError(
            "Authority escalation prohibited: assessment cannot claim execution authority"
        )

    # 2. Gate validation: must be ACCEPT_FOR_DEVELOPMENT
    disposition = assessment.get("disposition")
    if disposition != "ACCEPT_FOR_DEVELOPMENT":
        raise IngestionError(
            f"Candidate cannot be developed: disposition is {disposition!r}, "
            "must be 'ACCEPT_FOR_DEVELOPMENT'"
        )

    candidate_id = candidate.get("candidate_id", "unknown_candidate")
    objective = candidate.get("objective", "")
    text = candidate.get("text", "")
    assumptions = candidate.get("assumptions", [])
    constraints = candidate.get("verified_constraints", [])
    parent_req = candidate.get("parent_request_id", "")

    # 3. Create Idea model with strict epistemic tagging
    clean_id = candidate_id.replace("/", "-")
    idea_id = f"create-{clean_id}"
    title = f"Sandbox Prototype for {clean_id}"

    idea = Idea(
        id=idea_id,
        title=title,
        description=text,
        problem_framing=objective,
        core_mechanism=f"Exploratory mechanism based on candidate {candidate_id}",
        operator_used="deliberate_sandbox_development",
        parent_ids=[candidate_id],
        origin="howldream",
        epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
        assumptions=list(assumptions),
        constraints=list(constraints),
        speculations=[
            "Exploration hypothesis requires controlled sandbox validation before any production consideration."
        ],
        evidence_needs=[
            f"Independent verification of assumptions: {', '.join(assumptions) if assumptions else 'None declared'}"
        ],
        unanswered_questions=[
            "What are the precise latency and failure boundaries in staging?"
        ],
        status=ConceptStatus.CANDIDATE,
    )

    # 4. Record Lineage in LineageGraph
    graph = LineageGraph()
    parent_idea = Idea(
        id=candidate_id,
        title=f"DREAM Candidate ({candidate_id})",
        description=text,
        origin="howldream",
        epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
        operator_used="howldream_exploration",
    )
    graph.add_idea(parent_idea)
    graph.add_idea(idea)
    graph.add_edge(
        candidate_id,
        idea_id,
        operator="deliberate_sandbox_development",
        rationale="Candidate accepted by HowlFrame evaluation for deliberate sandbox development",
    )

    # 5. Formulate Deliberate Sandbox Plan (Design, Test Spec, Architecture Proposal)
    prototype_design = {
        "prototype_id": f"proto-{idea_id}",
        "target_sandbox_environment": "isolated_local_testbed",
        "implementation_steps": [
            "1. Instantiate mock service harness simulating intermittent deployment failures.",
            "2. Implement diagnostic hook matching candidate exploration proposal.",
            "3. Execute fault-injection sweep without remote egress or infrastructure mutation.",
        ],
        "isolation_controls": [
            "NO_PRODUCTION_DEPLOYMENT",
            "NO_IMPLICIT_NETWORK_EGRESS",
            "READ_ONLY_ACCESS_ONLY",
        ],
    }

    test_specification = [
        {
            "test_id": "test_sandbox_diagnostic_activation",
            "assertion": "Diagnostic captures failure metrics under simulated timeout",
            "expected_outcome": "PASS",
        },
        {
            "test_id": "test_sandbox_zero_side_effects",
            "assertion": "Diagnostic produces zero non-reproducible state mutations",
            "expected_outcome": "PASS",
        },
    ]

    architecture_proposal = (
        f"# Deliberate Sandbox Architecture Proposal for {idea_id}\n\n"
        f"**Origin**: HowlDream Speculative Exploration ({candidate_id})\n"
        f"**Evaluation**: HowlFrame ACCEPT_FOR_DEVELOPMENT ({assessment.get('assessment_id')})\n"
        f"**Epistemic Status**: IMAGINED_POSSIBILITY (Exploratory Prototype Only)\n\n"
        f"## Objective\n{objective}\n\n"
        f"## Proposed Mechanism\n{text}\n\n"
        f"## Verified Constraints\n"
        + "".join(f"- {c}\n" for c in constraints)
        + f"\n## Unresolved Assumptions\n"
        + "".join(f"- {a}\n" for a in assumptions)
        + "\n## Authority Boundary\n"
        "This proposal represents deliberate design in sandbox isolation. "
        "It carries NO EXECUTION OR DEPLOYMENT AUTHORITY in HowlPlane or HowlChangeOps."
    )

    now_str = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "howl.development_result/v1",
        "development_id": f"dev-{clean_id}",
        "source_candidate_id": candidate_id,
        "parent_request_id": parent_req,
        "origin": "howldream",
        "epistemic_status": EpistemicStatus.IMAGINED_POSSIBILITY.value,
        "authority": {
            "type": "ADVISORY",
            "executable": False,
        },
        "execution_authority": "NONE",
        "idea": idea.to_dict(),
        "lineage": {
            "parent_id": candidate_id,
            "child_id": idea_id,
            "ancestors": graph.get_ancestors(idea_id),
        },
        "sandbox_prototype_design": prototype_design,
        "test_specification": test_specification,
        "architecture_proposal": architecture_proposal,
        "provenance": {
            "candidate_id": candidate_id,
            "assessment_id": assessment.get("assessment_id"),
            "parent_request_id": parent_req,
            "developed_at": now_str,
            "system": "howlcreate",
        },
    }
