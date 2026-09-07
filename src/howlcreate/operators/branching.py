"""Independent Branching Operator: Generates unconstrained, isolated solution branches."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class IndependentBranchingOperator(BaseOperator):
    """Explores solution branches independently to prevent anchor bias and premature convergence."""

    def __init__(self, branch_archetype: str = "Explorer"):
        super().__init__(OperatorType.INDEPENDENT_BRANCHING, f"branching_{branch_archetype.lower()}")
        self.branch_archetype = branch_archetype

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        params = parameters or {}
        focus_domain = params.get("focus_domain", "unconstrained architectural innovation")

        prompt = (
            f"You are an Independent Creative Explorer in HowlCreate operating under the persona: '{self.branch_archetype}'.\n\n"
            f"Problem: \"{problem}\"\n"
            f"Exploration Focus: {focus_domain}\n\n"
            f"Rules:\n"
            f"1. Generate 2 to 3 genuinely distinct approaches. Do NOT produce slight variations of the same idea.\n"
            f"2. Clearly identify what is speculative versus grounded.\n"
            f"3. State what makes each approach fundamentally different from the status quo.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Distinct Concept Title",\n'
            f'      "description": "Thorough concept description",\n'
            f'      "core_mechanism": "How it actually works",\n'
            f'      "unconventional_aspect": "Why this is structurally different",\n'
            f'      "assumptions": ["Underlying assumptions"],\n'
            f'      "speculations": ["Speculative leaps"],\n'
            f'      "evidence_needs": ["What needs to be tested"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.85)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            idea = Idea(
                id=c_id,
                title=raw.get("title", f"{self.branch_archetype} Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                origin=f"branch:{self.branch_archetype.lower()}",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                assumptions=raw.get("assumptions", []),
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.INDEPENDENT_BRANCHING,
            ideas=ideas,
            metadata={"archetype": self.branch_archetype},
        )
