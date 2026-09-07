"""Simplification Operator: Dissolving problems rather than solving them."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class SimplificationOperator(BaseOperator):
    """Explores how the problem could disappear entirely rather than requiring an elaborate solution."""

    def __init__(self):
        super().__init__(OperatorType.SIMPLIFICATION, "simplification_operator")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        prompt = (
            f"You are the Simplification & Dissolution Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"\n\n"
            f"Core Question:\n"
            f"Instead of building complex machinery to solve this problem, how can the need for this problem to exist be eliminated entirely?\n"
            f"What structural, architectural, or incentive shift makes this whole issue irrelevant?\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Problem Dissolution Concept",\n'
            f'      "eliminated_need": "What burdensome requirement was removed",\n'
            f'      "description": "How the problem disappears",\n'
            f'      "core_mechanism": "Minimal mechanism replacing the problem space",\n'
            f'      "speculations": ["Speculative assumptions"],\n'
            f'      "evidence_needs": ["Empirical verification needed"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.7)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            eliminated = raw.get("eliminated_need", "")
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Dissolution Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                origin="simplification:dissolve",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                mutations=[f"Eliminated requirement: {eliminated}"] if eliminated else [],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.SIMPLIFICATION,
            ideas=ideas,
        )
