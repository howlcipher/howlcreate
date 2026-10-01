"""Multi-dimensional evaluation, uncertainty tracking, and convergence engine."""

from __future__ import annotations

import json
import math

from typing import Dict, List, Optional, Tuple
from howlcreate.engine.dedup import ConceptDeduplicator
from howlcreate.models.idea import (
    ConceptEvaluation,
    ConceptStatus,
    Idea,
    ScoreDetail,
)
from howlcreate.models.run import ConvergenceDecision
from howlcreate.providers.base import BaseProvider


class ConvergenceEngine:
    """Evaluates candidates across multiple dimensions and converges to a diverse finalist set."""

    DEFAULT_DIMENSIONS = [
        "novelty",
        "feasibility",
        "usefulness",
        "simplicity",
        "strategic_fit",
    ]

    DIMENSION_WEIGHTS = {
        "novelty": 0.25,
        "feasibility": 0.25,
        "usefulness": 0.25,
        "simplicity": 0.10,
        "strategic_fit": 0.15,
    }

    def __init__(
        self,
        deduplicator: Optional[ConceptDeduplicator] = None,
        top_n: int = 3,
        ecosystem_fit_weight: float = 0.0,
    ):
        self.deduplicator = deduplicator or ConceptDeduplicator()
        self.top_n = top_n
        if not 0 <= ecosystem_fit_weight <= 1:
            raise ValueError("ecosystem_fit_weight must be between zero and one")
        self.dimensions = list(self.DEFAULT_DIMENSIONS)
        self.weights = {
            key: value * (1 - ecosystem_fit_weight) for key, value in self.DIMENSION_WEIGHTS.items()
        }
        if ecosystem_fit_weight:
            self.dimensions.append("ecosystem_fit")
            self.weights["ecosystem_fit"] = ecosystem_fit_weight

    def evaluate_idea(
        self,
        idea: Idea,
        problem: str,
        provider: BaseProvider,
        evaluator_id: str = "evaluator_primary",
        supplied_data: dict | None = None,
        evaluation_execution: dict | None = None,
    ) -> ConceptEvaluation:
        """Score an idea across independent dimensions, preserving rationales and uncertainty."""
        prompt = (
            f"You are the Concept Evaluator in HowlCreate.\n\n"
            f'Problem: "{problem}"\n\n'
            f"Candidate Concept:\n"
            f"- Title: {idea.title}\n"
            f"- Description: {idea.description}\n"
            f"- Mechanism: {idea.core_mechanism}\n"
            f"- Origin: {idea.origin}\n"
            f"- Epistemic Status: {idea.epistemic_status.value}\n"
            f"- Criticisms: {', '.join(idea.criticisms) or 'None recorded'}\n\n"
            f"Evaluate across dimensions (0.0 to 1.0):\n"
            f"1. novelty: How genuinely different is this from standard solutions?\n"
            f"2. feasibility: Can this realistically be implemented with known technology?\n"
            f"3. usefulness: How substantial is the real-world value or impact?\n"
            f"4. simplicity: Is the mechanism elegant and minimal, or overcomplicated?\n"
            f"5. strategic_fit: Does this fit the supplied user objective and constraints?\n\n"
            f"CALIBRATION INSTRUCTIONS (Differentiate strictly across the 0.0 - 1.0 range):\n"
            f"- DO NOT assign uniform scores. Evaluate each dimension independently.\n"
            f"- Ideas with high complexity or ungrounded claims MUST score low on feasibility/simplicity (0.2-0.5).\n"
            f"- Obvious, generic, or conventional proposals MUST score low on novelty (0.1-0.4).\n"
            f"- Off-target or irrelevant concepts MUST score low on usefulness/strategic_fit (0.1-0.4).\n"
            f"- Reserve high scores (>= 0.85) strictly for genuinely exceptional, defensible concepts.\n"
            f"- Compute genuine, differentiated floating-point values for each dimension based on this specific concept.\n\n"
            f"For each score, provide uncertainty (0.0 = high confidence, 1.0 = highly uncertain estimate).\n\n"
            f"Return valid JSON (replace placeholder types with your evaluated float numbers):\n"
            f"{{\n"
            f'  "scores": {{\n'
            f'    "novelty": {{"score": 0.0, "rationale": "...", "uncertainty": 0.0}},\n'
            f'    "feasibility": {{"score": 0.0, "rationale": "...", "uncertainty": 0.0}},\n'
            f'    "usefulness": {{"score": 0.0, "rationale": "...", "uncertainty": 0.0}},\n'
            f'    "simplicity": {{"score": 0.0, "rationale": "...", "uncertainty": 0.0}},\n'
            f'    "strategic_fit": {{"score": 0.0, "rationale": "...", "uncertainty": 0.0}}\n'
            f"  }},\n"
            f'  "strengths": ["Strength 1", "Strength 2"],\n'
            f'  "weaknesses": ["Weakness 1"],\n'
            f'  "critical_risks": ["Risk 1"]\n'
            f"}}\n"
        )

        if supplied_data is None:
            resp = provider.generate_for("evaluation", prompt, json_mode=True, temperature=0.3)
            data = resp.extract_json() or {}
            evaluation_execution = resp.metadata.get("execution")
        else:
            data = supplied_data

        raw_scores = data.get("scores", {})
        scores: Dict[str, ScoreDetail] = {}

        for dim in self.dimensions:
            dim_data = raw_scores.get(dim)
            if not isinstance(dim_data, dict):
                raise ValueError("incomplete evaluation; no scores fabricated")
            score, uncertainty = dim_data.get("score"), dim_data.get("uncertainty")
            if any(
                type(v) not in {int, float} or not math.isfinite(v) or not 0 <= v <= 1
                for v in (score, uncertainty)
            ):
                raise ValueError("invalid evaluation numeric range")
            rationale = dim_data.get("rationale")
            if not isinstance(rationale, str):
                raise ValueError("missing evaluation rationale")
            scores[dim] = ScoreDetail(
                dimension=dim, score=score, rationale=rationale, uncertainty=uncertainty
            )

        composite = sum(scores[d].score * self.weights[d] for d in scores)

        eval_obj = ConceptEvaluation(
            evaluator_id=evaluator_id,
            scores=scores,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            critical_risks=data.get("critical_risks", []),
            composite_score=round(composite, 3),
        )

        idea.provenance.setdefault("evaluation_executions", []).append(evaluation_execution)
        idea.evaluations.append(eval_obj)
        return eval_obj

    def converge(
        self,
        ideas: List[Idea],
        problem: str,
        provider: BaseProvider,
    ) -> Tuple[List[Idea], Dict[str, ConvergenceDecision]]:
        """Evaluate all ideas, cluster by similarity, and select diverse finalists with explicit rationale."""
        if not ideas:
            return [], {}

        # One bounded request per batch, preserving each candidate's identity.
        pending = [idea for idea in ideas if not idea.evaluations]
        errors = []
        for offset in range(0, len(pending), 8):
            batch = pending[offset : offset + 8]
            payload = [
                {
                    "id": idea.id,
                    "title": idea.title,
                    "description": idea.description,
                    "mechanism": idea.core_mechanism,
                    "assumptions": idea.assumptions,
                    "criticisms": idea.criticisms,
                    "epistemic_status": idea.epistemic_status.value,
                }
                for idea in batch
            ]
            prompt = (
                f'Problem: "{problem}"\n'
                "Evaluate each candidate against the supplied objective, not ecosystem membership. "
                'Return {"evaluations": {candidate_id: {"scores": {dimension: '
                '{"score": number, "uncertainty": number, "rationale": string}}, '
                '"strengths": [], "weaknesses": [], "critical_risks": []}}}. '
                "Scores and uncertainty must be between 0 and 1. Dimensions: "
                + ", ".join(self.dimensions)
                + ". strategic_fit means alignment with this user's objective and constraints. "
                "novelty means difference from conventional approaches; feasibility means "
                "implementability; usefulness means user value; simplicity means minimal complexity. "
                "Distinguish scores and state uncertainty; do not invent supporting evidence.\n"
                "CANDIDATES_JSON:\n" + json.dumps(payload)
            )
            response = provider.generate_for(
                "evaluation_batch", prompt, json_mode=True, temperature=0.3
            )
            data = response.extract_json() or {}
            evaluations = data.get("evaluations", {})
            if not isinstance(evaluations, dict):
                evaluations = {}
            if set(evaluations) != {idea.id for idea in batch}:
                errors.append("evaluation candidate IDs mismatch")
            for idea in batch:
                try:
                    value = evaluations[idea.id]
                    self.evaluate_idea(
                        idea,
                        problem,
                        provider,
                        supplied_data=value,
                        evaluation_execution=response.metadata.get("execution"),
                    )
                except (KeyError, TypeError, ValueError):
                    errors.append("incomplete evaluation")
        if errors:
            raise ValueError("incomplete batch evaluation; valid scores retained, none fabricated")

        # 2. Cluster to avoid duplicate finalists
        clusters, outliers = self.deduplicator.cluster_ideas(ideas)

        # 3. Pick top representative per cluster
        cluster_champions: List[Idea] = []
        for cluster_id, members in clusters.items():
            sorted_members = sorted(members, key=lambda x: x.composite_score(), reverse=True)
            champion = sorted_members[0]
            cluster_champions.append(champion)

        # Sort champions by composite score
        sorted_champions = sorted(
            cluster_champions, key=lambda x: x.composite_score(), reverse=True
        )

        finalists: List[Idea] = []
        finalist_ids: set[str] = set()
        represented_clusters: set[str] = set()

        # Take top cluster champions from distinct clusters up to top_n - 1
        champion_limit = max(1, self.top_n - 1) if len(sorted_champions) > 1 else self.top_n
        for champ in sorted_champions:
            champ_cluster = champ.cluster_id or champ.id
            if champ_cluster not in represented_clusters and len(finalists) < champion_limit:
                finalists.append(champ)
                finalist_ids.add(champ.id)
                represented_clusters.add(champ_cluster)

        # Look for high-novelty wildcard from unrepresented clusters/outliers first
        remaining_unrepresented = [
            i
            for i in ideas
            if i.id not in finalist_ids and (i.cluster_id or i.id) not in represented_clusters
        ]
        pool_for_wildcard = (
            remaining_unrepresented
            if remaining_unrepresented
            else [i for i in ideas if i.id not in finalist_ids]
        )

        if pool_for_wildcard and len(finalists) < self.top_n:
            wildcard = max(
                pool_for_wildcard,
                key=lambda x: max(
                    (
                        e.scores.get("novelty", ScoreDetail("novelty", 0.0)).score
                        for e in x.evaluations
                    ),
                    default=0.0,
                ),
            )
            finalists.append(wildcard)
            finalist_ids.add(wildcard.id)

        # Ensure we do not exceed top_n
        finalists = finalists[: self.top_n]

        # 4. Formulate convergence decisions with inspectable rationale
        decisions: Dict[str, ConvergenceDecision] = {}

        for idea in ideas:
            if idea.id in finalist_ids:
                idea.status = ConceptStatus.FINALIST
                eval_inst = idea.evaluations[-1] if idea.evaluations else None
                strengths = eval_inst.strengths if eval_inst else []
                risks = eval_inst.critical_risks if eval_inst else []
                score = idea.composite_score()

                decisions[idea.id] = ConvergenceDecision(
                    idea_id=idea.id,
                    status=ConceptStatus.FINALIST.value,
                    rationale=(
                        f"Selected as top finalist (composite score: {score:.2f}). "
                        f"Demonstrated distinct strategic mechanism in {idea.cluster_id or 'unique cluster'} "
                        f"with superior balance of novelty and feasibility."
                    ),
                    strengths_emphasized=strengths,
                    risks_noted=risks,
                )
            else:
                idea.status = ConceptStatus.SET_ASIDE
                score = idea.composite_score()
                decisions[idea.id] = ConvergenceDecision(
                    idea_id=idea.id,
                    status=ConceptStatus.SET_ASIDE.value,
                    rationale=(
                        f"Set aside (score: {score:.2f}). "
                        f"Alternative concept in {idea.cluster_id or 'same cluster'} provided stronger feasibility "
                        f"or clearer verification boundaries."
                    ),
                    risks_noted=idea.criticisms[:2],
                )

        return finalists, decisions
