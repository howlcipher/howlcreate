"""Substitution Operator: Swaps out conventional components with alternative abstractions."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class SubstitutionOperator(BaseOperator):
    """Substitutes actors, processes, technologies, incentives, or abstractions."""

    def __init__(self):
        super().__init__(OperatorType.SUBSTITUTION, "substitution_operator")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        prompt = (
            f"You are the Substitution Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"\n\n"
            f"Substitution Protocol:\n"
            f"Identify a standard component (e.g. human manager, centralized database, legal contract, salary, synchronous meeting).\n"
            f"Replace that component with a fundamentally different actor or medium (e.g. mathematical proof, automated escrow, stigmergic state log, local-first cache).\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Substituted Architecture Title",\n'
            f'      "conventional_element": "What standard element was removed",\n'
            f'      "substituted_replacement": "What unexpected medium replaces it",\n'
            f'      "description": "Full description of substituted approach",\n'
            f'      "core_mechanism": "Working mechanism of substitution",\n'
            f'      "speculations": ["Speculative assumptions"],\n'
            f'      "evidence_needs": ["Empirical verification needed"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.75)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            conv = raw.get("conventional_element", "")
            sub = raw.get("substituted_replacement", "")
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Substitution Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                origin=f"substitution:{sub[:20]}",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                mutations=[f"Substituted '{conv}' with '{sub}'"] if conv and sub else [],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.SUBSTITUTION,
            ideas=ideas,
        )
