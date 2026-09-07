"""Adversarial Critique & Defensive Mutation Operator."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import ConceptStatus, EpistemicStatus, Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.operators.base import BaseOperator
from howlcreate.providers.base import BaseProvider


class AdversarialCritiqueOperator(BaseOperator):
    """Subject concepts to stress-testing, brittleness discovery, and defensive hardening."""

    def __init__(self):
        super().__init__(OperatorType.ADVERSARIAL_CRITIQUE, "adversarial_critique")

    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        if not context_ideas:
            return OperatorResult(operator_type=OperatorType.ADVERSARIAL_CRITIQUE, ideas=[])

        target_idea = context_ideas[0]

        prompt = (
            f"You are the Adversarial Red-Team Critic in HowlCreate.\n\n"
            f"Core Problem: \"{problem}\"\n"
            f"Target Concept Under Attack:\n"
            f"- Title: {target_idea.title}\n"
            f"- Description: {target_idea.description}\n"
            f"- Mechanism: {target_idea.core_mechanism}\n\n"
            f"Attack Protocol:\n"
            f"1. What is the single point of catastrophic failure or brittle assumption?\n"
            f"2. How would an adversary or parasitic actor game or exploit this mechanism?\n"
            f"3. What hidden cost, cognitive friction, or adoption barrier is overlooked?\n"
            f"4. DEFENSIVE MUTATION: Formulate an evolved, hardened mutation of this concept that directly neutralizes these attacks while preserving its core insight.\n\n"
            f"Return valid JSON:\n"
            f"{{\n"
            f'  "criticism": {{\n'
            f'    "vulnerabilities": ["Vulnerability 1", "Vulnerability 2"],\n'
            f'    "unconsidered_costs": ["Overlooked cost or friction"],\n'
            f'    "defensive_mutations": ["Adaptation 1", "Adaptation 2"]\n'
            f'  }},\n'
            f'  "hardened_idea": {{\n'
            f'    "title": "Hardened Concept Title",\n'
            f'    "description": "Hardened concept description",\n'
            f'    "core_mechanism": "Hardened mechanism with safeguards",\n'
            f'    "safeguards_added": ["Safeguard A", "Safeguard B"],\n'
            f'    "speculations": ["Speculative properties"],\n'
            f'    "evidence_needs": ["Empirical verification needed"]\n'
            f'  }}\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.7)
        data = resp.extract_json() or {}

        critique_data = data.get("criticism") or data.get("critique") or {}
        vulns = critique_data.get("vulnerabilities", [])
        costs = critique_data.get("unconsidered_costs", [])
        mutations = critique_data.get("defensive_mutations", [])

        # Record criticisms on the original idea
        target_idea.criticisms.extend(vulns + costs)
        target_idea.status = ConceptStatus.CHALLENGED

        ideas: List[Idea] = []
        raw_hardened = data.get("hardened_idea")
        if raw_hardened:
            c_id = f"idea-{uuid.uuid4().hex[:6]}"
            hardened = Idea(
                id=c_id,
                title=raw_hardened.get("title", f"Hardened {target_idea.title}"),
                description=raw_hardened.get("description", ""),
                problem_framing=problem,
                core_mechanism=raw_hardened.get("core_mechanism", ""),
                operator_used=self.name,
                parent_ids=[target_idea.id],
                origin=f"hardened:{target_idea.id}",
                epistemic_status=EpistemicStatus.HYPOTHESIS,
                status=ConceptStatus.MUTATED,
                mutations=mutations + raw_hardened.get("safeguards_added", []),
                speculations=raw_hardened.get("speculations", []),
                evidence_needs=raw_hardened.get("evidence_needs", []),
            )
            ideas.append(hardened)

        return OperatorResult(
            operator_type=OperatorType.ADVERSARIAL_CRITIQUE,
            ideas=ideas,
            mutations=mutations,
            metadata={"target_id": target_idea.id, "vulnerabilities": vulns},
        )
