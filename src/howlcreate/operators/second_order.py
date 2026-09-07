"""Second-Order Exploration Operator: Projects downstream and systemic consequences."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class SecondOrderOperator(BaseOperator):
    """Explores what happens after the obvious first-order consequence succeeds at scale."""

    def __init__(self):
        super().__init__(OperatorType.SECOND_ORDER_EXPLORATION, "second_order_explorer")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        context_idea = context_ideas[0] if context_ideas else None
        target_context = f"\nFocus Idea to extrapolate: '{context_idea.title}' - {context_idea.description}" if context_idea else ""

        prompt = (
            f"You are the Second-Order Exploration Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"{target_context}\n\n"
            f"Thinking Protocol:\n"
            f"First-order thinking asks: What happens immediately when we solve this?\n"
            f"Second-order thinking asks: And then what? What feedback loops, behavioral adaptations, or emergent secondary equilibria occur when millions adopt this?\n\n"
            f"Your task:\n"
            f"1. Map out 1-2 major second-order shifts.\n"
            f"2. Formulate a proactive concept designed specifically to capitalize on or stabilize that second-order equilibrium.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Second-Order Concept Title",\n'
            f'      "second_order_shift": "The systemic ripple effect anticipated",\n'
            f'      "description": "Full description of proactive concept",\n'
            f'      "core_mechanism": "Mechanism addressing the emergent equilibrium",\n'
            f'      "speculations": ["Speculative feedback loops"],\n'
            f'      "evidence_needs": ["Empirical indicators to monitor"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.75)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            p_ids = [context_idea.id] if context_idea else []
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Second-Order Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                parent_ids=p_ids,
                origin=f"second_order:{context_idea.id if context_idea else 'global'}",
                epistemic_status=EpistemicStatus.PREDICTION,
                mutations=[f"Anticipated shift: {raw.get('second_order_shift', '')}"],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.SECOND_ORDER_EXPLORATION,
            ideas=ideas,
        )
