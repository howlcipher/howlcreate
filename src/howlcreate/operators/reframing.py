"""Reframing Operator: Multi-perspective problem formulation."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType, ReframingLens
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class ReframingOperator(BaseOperator):
    """Re-articulates problems through contrasting viewpoints and stakeholder lenses."""

    DEFAULT_PERSPECTIVES = [
        "Adversary / Opportunist looking for loopholes",
        "Resource-constrained contributor with near-zero budget/compute",
        "Future observer looking back from 10 years ahead",
        "Outsider from an unrelated discipline (e.g. marine biologist or civil engineer)",
        "Extreme pragmatist focused strictly on immediate tangible utility",
    ]

    def __init__(self):
        super().__init__(OperatorType.REFRAMING, "reframing_operator")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        params = parameters or {}
        perspectives = params.get("perspectives", self.DEFAULT_PERSPECTIVES)
        perspectives_str = "\n".join(f"- {p}" for p in perspectives)

        prompt = (
            f"You are the Reframing Operator in HowlCreate.\n\n"
            f"Original Problem: \"{problem}\"\n\n"
            f"Reflect on this problem through the following perspectives:\n"
            f"{perspectives_str}\n\n"
            f"Your task:\n"
            f"1. Generate 3 to 5 distinct Reframing Lenses that change what is actually being solved.\n"
            f"2. For each lens, generate 1 solution concept that would only occur to someone viewing the problem through that lens.\n\n"
            f"Return valid JSON matching this schema:\n"
            f"{{\n"
            f'  "reframings": [\n'
            f'    {{\n'
            f'      "perspective": "Name of perspective",\n'
            f'      "reframed_question": "How can we...?",\n'
            f'      "core_focus": "The central insight or objective under this lens"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Concept Name",\n'
            f'      "perspective_origin": "Which lens inspired this",\n'
            f'      "description": "Concept description",\n'
            f'      "core_mechanism": "How it addresses the reframed question",\n'
            f'      "speculations": ["Speculative assumptions or predictions"],\n'
            f'      "evidence_needs": ["Empirical verification needed"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True)
        data = resp.extract_json() or {}

        reframings: List[ReframingLens] = []
        for raw in data.get("reframings", []):
            lens_id = f"lens-{uuid.uuid4().hex[:6]}"
            reframings.append(
                ReframingLens(
                    lens_id=lens_id,
                    perspective=raw.get("perspective", "Alternative View"),
                    reframed_question=raw.get("reframed_question", problem),
                    core_focus=raw.get("core_focus", ""),
                )
            )

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Reframed Concept"),
                description=raw.get("description", ""),
                problem_framing=raw.get("perspective_origin", problem),
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                origin=f"reframe:{raw.get('perspective_origin', 'general')}",
                epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.REFRAMING,
            ideas=ideas,
            reframings=reframings,
            metadata={"raw_response_tokens": resp.completion_tokens},
        )
