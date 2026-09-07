"""Forced Combination Operator: Synthesizes orthogonal or unrelated ideas."""

from __future__ import annotations

import itertools
import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import ConceptStatus, EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class ForcedCombinationOperator(BaseOperator):
    """Deliberately collides two or more distinct concepts to produce unexpected hybrids."""

    def __init__(self):
        super().__init__(OperatorType.FORCED_COMBINATION, "forced_combination")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        if not context_ideas or len(context_ideas) < 2:
            return OperatorResult(operator_type=OperatorType.FORCED_COMBINATION, ideas=[])

        # Pick two distinct ideas to combine
        pairs = list(itertools.combinations(context_ideas[:4], 2))
        idea_a, idea_b = pairs[0] if pairs else (context_ideas[0], context_ideas[1])

        prompt = (
            f"You are the Forced Combination Operator in HowlCreate.\n\n"
            f"Core Problem: \"{problem}\"\n\n"
            f"Idea A:\n"
            f"- Title: {idea_a.title}\n"
            f"- Mechanism: {idea_a.core_mechanism or idea_a.description}\n\n"
            f"Idea B:\n"
            f"- Title: {idea_b.title}\n"
            f"- Mechanism: {idea_b.core_mechanism or idea_b.description}\n\n"
            f"Your task:\n"
            f"Deliberately collide Idea A and Idea B into a single hybrid concept. Do NOT simply glue them together; create an emergent mechanism where Idea A solves the weakness of Idea B or unlocks a capability neither had alone.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Emergent Hybrid Title",\n'
            f'      "description": "Integrated concept description",\n'
            f'      "core_mechanism": "How the two components reinforce each other",\n'
            f'      "emergent_advantage": "What becomes possible only with this combination",\n'
            f'      "speculations": ["Speculative properties"],\n'
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
            idea = Idea(
                id=c_id,
                title=raw.get("title", f"Hybrid: {idea_a.title} + {idea_b.title}"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                parent_ids=[idea_a.id, idea_b.id],
                origin=f"combination:{idea_a.id}+{idea_b.id}",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                status=ConceptStatus.COMBINED,
                mutations=[f"Combined '{idea_a.title}' with '{idea_b.title}'"],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.FORCED_COMBINATION,
            ideas=ideas,
            metadata={"parents": [idea_a.id, idea_b.id]},
        )
