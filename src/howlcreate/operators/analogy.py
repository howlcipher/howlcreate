"""Analogical Reasoning Operator: Cross-domain structural mapping."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class AnalogicalReasoningOperator(BaseOperator):
    """Imports structural solutions from unrelated physical, biological, and economic domains."""

    DOMAINS = [
        ("Biology & Mycology", "Mycelial nutrient sharing, mycorrhizal fungal-root barter networks, stigmergy in ant colonies"),
        ("Manufacturing & Supply Chain", "Kanban pull systems, decoupling buffers, Toyota Kata, poka-yoke error prevention"),
        ("Game Design & Game Theory", "Fog of war, asymmetric player abilities, emergent gameplay, mechanism design"),
        ("Ecology & Evolutionary Dynamics", "Niche differentiation, adaptive radiation, trophic cascades, commensalism"),
        ("Civil & Maritime Engineering", "Bulkheads, lighthouse navigation, decentralized canal lock scheduling"),
    ]

    def __init__(self):
        super().__init__(OperatorType.ANALOGICAL_REASONING, "analogical_reasoning")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        domains_formatted = "\n".join(f"- **{name}**: {desc}" for name, desc in self.DOMAINS)

        prompt = (
            f"You are the Analogical Reasoning Operator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"\n\n"
            f"Domain Sources for Analogy:\n{domains_formatted}\n\n"
            f"Your task:\n"
            f"1. Select 2 distinct domains above.\n"
            f"2. For each, identify a structural isomorphism (how the dynamics of the problem mirror dynamics in that domain).\n"
            f"3. Formulate a creative concept that directly translates that domain's mechanism into a computational or organizational solution.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "ideas": [\n'
            f'    {{\n'
            f'      "title": "Concept Title",\n'
            f'      "source_domain": "Name of source domain",\n'
            f'      "analogy_explanation": "How the biological/engineering principle maps to this problem",\n'
            f'      "description": "Full description of the idea",\n'
            f'      "core_mechanism": "Concrete working mechanism",\n'
            f'      "speculations": ["Speculative benefits"],\n'
            f'      "evidence_needs": ["Empirical verification tests"]\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.8)
        data = resp.extract_json() or {}

        ideas: List[Idea] = []
        for raw in data.get("ideas", []):
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            src_domain = raw.get("source_domain", "External Domain")
            analogy = raw.get("analogy_explanation", "")
            idea = Idea(
                id=c_id,
                title=raw.get("title", f"{src_domain} Analogy Concept"),
                description=raw.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw.get("core_mechanism", ""),
                operator_used=self.name,
                origin=f"analogy:{src_domain.lower()[:20]}",
                epistemic_status=EpistemicStatus.ANALOGY,
                analogies=[f"{src_domain}: {analogy}"],
                speculations=raw.get("speculations", []),
                evidence_needs=raw.get("evidence_needs", []),
            )
            ideas.append(idea)

        return OperatorResult(
            operator_type=OperatorType.ANALOGICAL_REASONING,
            ideas=ideas,
            metadata={"domains_considered": [d[0] for d in self.DOMAINS]},
        )
