"""Assumption Extraction and Inversion Operators."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import AssumptionItem, OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class AssumptionOperator(BaseOperator):
    """Identifies explicit and implicit assumptions and explores what happens when inverted."""

    def __init__(self):
        super().__init__(OperatorType.ASSUMPTION_EXTRACTION, "assumption_operator")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        prompt = (
            f"You are the Assumption Extraction & Inversion Operator in the Howl ecosystem.\n\n"
            f"Problem Statement: \"{problem}\"\n\n"
            f"Your task:\n"
            f"1. Identify 3 to 5 core explicit and implicit assumptions people naturally take for granted when considering this problem.\n"
            f"2. For each assumption, provide 1-2 radical inversions: what happens if the assumption is false, reversed, removed, or exaggerated?\n"
            f"3. Formulate 1-2 novel solution concepts directly derived from these inversions.\n\n"
            f"Return ONLY valid JSON matching this schema:\n"
            f"{{\n"
            f'  "assumptions": [\n'
            f'    {{\n'
            f'      "statement": "Explicit or implicit assumption",\n'
            f'      "is_implicit": true,\n'
            f'      "vulnerability": "Why this assumption is brittle or limits the search",\n'
            f'      "inversions": ["Inverted premise 1", "Inverted premise 2"]\n'
            f'    }}\n'
            f'  ],\n'
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Concept Name",\n'
            f'      "description": "Concept description",\n'
            f'      "core_mechanism": "How it works when the assumption is inverted",\n'
            f'      "changed_assumptions": ["Assumed X -> instead Y"],\n'
            f'      "speculations": ["What is speculative here"],\n'
            f'      "evidence_needs": ["What empirical test would verify this"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True)
        data = resp.extract_json() or {}

        raw_assumptions = data.get("assumptions", [])
        assumption_items: List[AssumptionItem] = []
        for i, raw in enumerate(raw_assumptions):
            a_id = f"asm-{uuid.uuid4().hex[:6]}"
            stmt = raw.get("statement", f"Assumption {i+1}")
            invs = raw.get("inversions", [])
            vuln = raw.get("vulnerability", "")
            implicit = raw.get("is_implicit", True)
            assumption_items.append(
                AssumptionItem(
                    id=a_id,
                    statement=stmt,
                    is_implicit=implicit,
                    inversions=invs,
                    vulnerability=vuln,
                )
            )

        # Build ideas if generated
        raw_ideas = data.get("ideas", [])
        ideas: List[Idea] = []
        for raw_idea in raw_ideas:
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            title = raw_idea.get("title", "Inverted Assumption Concept")
            desc = raw_idea.get("description", "")
            mech = raw_idea.get("core_mechanism", "")
            changed_asms = raw_idea.get("changed_assumptions", [])
            specs = raw_idea.get("speculations", [])
            evid = raw_idea.get("evidence_needs", [])

            idea = Idea(
                id=c_id,
                title=title,
                description=desc,
                problem_framing=problem,
                core_mechanism=mech,
                operator_used=self.name,
                origin="assumption_inversion",
                epistemic_status=EpistemicStatus.HYPOTHESIS,
                assumptions=[a.statement for a in assumption_items],
                changed_assumptions=changed_asms,
                speculations=specs,
                evidence_needs=evid,
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.ASSUMPTION_EXTRACTION,
            ideas=ideas,
            assumptions=assumption_items,
            metadata={"raw_response_tokens": resp.completion_tokens},
        )
