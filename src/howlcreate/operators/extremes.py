"""Extreme Solutions Operator: Formulates radical caricatures to expose governing principles."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class ExtremeSolutionsOperator(BaseOperator):
    """Generates deliberately extreme or unrealistic ideas to strip away dogma and expose principles."""

    def __init__(self):
        super().__init__(OperatorType.EXTREME_SOLUTIONS, "extreme_solutions")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        prompt = (
            f"You are the Extreme Solutions Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"\n\n"
            f"Thinking Protocol:\n"
            f"Take any standard variable in this problem and dial it to either 0% or 10,000%.\n"
            f"Generate 1-2 extreme, borderline absurd solutions that no conventional committee would approve.\n"
            f"Then extract the REAL, usable principle hiding inside that extreme caricature.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Extreme Concept Title",\n'
            f'      "extreme_dimension": "What parameter was dialed to the absolute extreme",\n'
            f'      "description": "Full description of the radical caricature",\n'
            f'      "core_mechanism": "Concrete working mechanism",\n'
            f'      "usable_underlying_principle": "The rational engineering principle uncovered",\n'
            f'      "speculations": ["Speculative aspects"],\n'
            f'      "evidence_needs": ["Empirical verification needed"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.9)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            principle = raw.get("usable_underlying_principle", "")
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Extreme Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                origin=f"extreme:{raw.get('extreme_dimension', 'general')[:20]}",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                mutations=[f"Underlying Principle: {principle}"] if principle else [],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.EXTREME_SOLUTIONS,
            ideas=ideas,
        )
