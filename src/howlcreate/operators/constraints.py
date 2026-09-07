"""Constraint Mutation Operator: Stresses solutions under radically altered constraints."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class ConstraintMutationOperator(BaseOperator):
    """Mutates operational constraints to discover principles hidden by normal assumptions."""

    DEFAULT_MUTATIONS = [
        "Zero Internet / Completely Offline-first: Network is unavailable 99% of the time",
        "Zero Budget / Bootstrap: No capital expenditure, purely peer-to-peer or zero-cost primitives",
        "Extreme Asynchrony: Operations take months or years with no real-time coordination",
        "Total Privacy / Anonymity: Zero persistent identity or surveillance, strictly zero-knowledge",
        "Failure-Tolerant Swarms: Any node or agent can crash or defect at any moment with zero harm",
    ]

    def __init__(self):
        super().__init__(OperatorType.CONSTRAINT_MUTATION, "constraint_mutator")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        params = parameters or {}
        mutations = params.get("mutations", self.DEFAULT_MUTATIONS)
        mutations_str = "\n".join(f"- {m}" for m in mutations)

        seed_titles = [f"'{idea.title}'" for idea in (context_ideas or [])[:3]]
        context_str = f"\nExisting seed concepts to stress-test or mutate: {', '.join(seed_titles)}" if seed_titles else ""

        prompt = (
            f"You are the Constraint Mutation Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"{context_str}\n\n"
            f"Altered Constraints:\n{mutations_str}\n\n"
            f"Your task:\n"
            f"Formulate 2 to 3 concepts that thrive specifically under these radical constraint mutations.\n"
            f"Explain what fundamental principle emerges when the standard constraint is destroyed.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Concept Name",\n'
            f'      "constraint_applied": "Which constraint mutation",\n'
            f'      "description": "How the solution operates under this constraint",\n'
            f'      "core_mechanism": "Underlying mechanism",\n'
            f'      "underlying_principle": "What this reveals about the problem",\n'
            f'      "speculations": ["Speculative aspects"],\n'
            f'      "evidence_needs": ["Empirical verification needed"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.8)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            parent_ids = [idea.id for idea in (context_ideas or [])[:2]]
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Constraint-Mutated Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                parent_ids=parent_ids,
                origin=f"constraint:{raw.get('constraint_applied', 'general')[:20]}",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                constraints=[raw.get("constraint_applied", "")],
                mutations=[f"Constraint Mutation: {raw.get('constraint_applied', '')}"],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.CONSTRAINT_MUTATION,
            ideas=ideas,
            mutations=mutations,
        )
