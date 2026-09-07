"""Synthesis Operator: Integrates high-potential components into cohesive concepts."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import ConceptStatus, EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class SynthesisOperator(BaseOperator):
    """Synthesizes high-performing components from multiple branches into cohesive architectures."""

    def __init__(self):
        super().__init__(OperatorType.SYNTHESIS, "synthesis_operator")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        if not context_ideas:
            return OperatorResult(operator_type=OperatorType.SYNTHESIS, ideas=[])

        candidates = context_ideas[:5]
        ideas_summary = "\n".join(
            f"Idea {i+1} [ID: {c.id}]: '{c.title}'\n"
            f"  Core: {c.core_mechanism or c.description}\n"
            f"  Origin: {c.origin} | Strengths: {', '.join(c.mutations or ['novel angle'])}"
            for i, c in enumerate(candidates)
        )

        prompt = (
            f"You are the Synthesis Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"\n\n"
            f"Pool of Candidate Concepts:\n{ideas_summary}\n\n"
            f"Synthesis Protocol:\n"
            f"1. Identify complementary strengths across these candidates (e.g. Concept A's incentive structure + Concept B's verification gate + Concept C's offline resilience).\n"
            f"2. Synthesize an integrated, unified concept that dissolves the trade-offs between them.\n"
            f"3. Note the exact parent IDs contributing to this synthesis.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Synthesized Concept Title",\n'
            f'      "parent_concept_ids": ["id-1", "id-2"],\n'
            f'      "description": "Comprehensive integrated concept description",\n'
            f'      "core_mechanism": "Unified mechanism resolving tensions",\n'
            f'      "integrated_strengths": "How it combines strengths",\n'
            f'      "speculations": ["Speculative benefits"],\n'
            f'      "evidence_needs": ["Empirical verification needed"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.7)
        data = resp.extract_json() or {}

        parent_ids = [c.id for c in candidates]
        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            claimed_parents = raw.get("parent_concept_ids", parent_ids[:2])
            # filter to parents that actually exist
            valid_parents = [p for p in claimed_parents if any(c.id == p for c in candidates)] or parent_ids[:2]
            idea = Idea(
                id=c_id,
                title=raw.get("title", "Synthesized Concept Architecture"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                parent_ids=valid_parents,
                origin=f"synthesis:{'+'.join(valid_parents[:2])}",
                epistemic_status=EpistemicStatus.HYPOTHESIS,
                status=ConceptStatus.COMBINED,
                mutations=[f"Synthesized strengths: {raw.get('integrated_strengths', '')}"],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.SYNTHESIS,
            ideas=ideas,
            metadata={"source_concept_count": len(candidates)},
        )
