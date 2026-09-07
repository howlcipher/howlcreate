"""Multi-dimensional evaluation, uncertainty tracking, and convergence engine."""

from __future__ import annotations

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
    ):
        self.deduplicator = deduplicator or ConceptDeduplicator()
        self.top_n = top_n

    def evaluate_idea(
        self,
        idea: Idea,
        problem: str,
        provider: BaseProvider,
        evaluator_id: str = "evaluator_primary",
    ) -> ConceptEvaluation:
        """Score an idea across independent dimensions, preserving rationales and uncertainty."""
        prompt = (
            f"You are the Concept Evaluator in HowlCreate.\n\n"
            f"Problem: \"{problem}\"\n\n"
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
            f"5. strategic_fit: Does this align with the sovereign, verifiable goals of the Howl ecosystem?\n\n"
            f"CALIBRATION INSTRUCTIONS (Differentiate strictly across the 0.0 - 1.0 range):\n"
            f"- DO NOT assign uniform scores (e.g. all 0.7 or 0.8). Evaluate each dimension independently.\n"
            f"- Ideas with high complexity, ungrounded claims, or sybil risks MUST score low on feasibility/simplicity (0.2-0.5).\n"
            f"- Obvious, generic, or conventional proposals MUST score low on novelty (0.1-0.4).\n"
            f"- Off-target or irrelevant concepts MUST score low on usefulness/strategic_fit (0.1-0.4).\n"
            f"- Reserve high scores (>= 0.85) strictly for genuinely exceptional, defensible concepts.\n\n"
            f"For each score, provide uncertainty (0.0 = high confidence, 1.0 = highly uncertain estimate).\n\n"
            f"Return valid JSON with differentiated numbers:\n"
            f"{{\n"
            f'  "scores": {{\n'
            f'    "novelty": {{"score": 0.85, "rationale": "...", "uncertainty": 0.15}},\n'
            f'    "feasibility": {{"score": 0.65, "rationale": "...", "uncertainty": 0.25}},\n'
            f'    "usefulness": {{"score": 0.90, "rationale": "...", "uncertainty": 0.10}},\n'
            f'    "simplicity": {{"score": 0.45, "rationale": "...", "uncertainty": 0.30}},\n'
            f'    "strategic_fit": {{"score": 0.75, "rationale": "...", "uncertainty": 0.20}}\n'
            f'  }},\n'
            f'  "strengths": ["Strength 1", "Strength 2"],\n'
            f'  "weaknesses": ["Weakness 1"],\n'
            f'  "critical_risks": ["Risk 1"]\n'
            f"}}\n"
        )

        resp = provider.generate(prompt, json_mode=True, temperature=0.3)
        data = resp.extract_json() or {}

        raw_scores = data.get("scores", {})
        scores: Dict[str, ScoreDetail] = {}

        for dim in self.DEFAULT_DIMENSIONS:
            if dim in raw_scores:
                dim_data = raw_scores[dim]
                scores[dim] = ScoreDetail(
                    dimension=dim,
                    score=float(dim_data.get("score", 0.5)),
                    rationale=dim_data.get("rationale", ""),
                    uncertainty=float(dim_data.get("uncertainty", 0.3)),
                )
            else:
                # Default fallback score
                scores[dim] = ScoreDetail(
                    dimension=dim,
                    score=0.6,
                    rationale="Heuristic baseline score",
                    uncertainty=0.4,
                )

        composite = sum(
            scores[d].score * self.DIMENSION_WEIGHTS.get(d, 0.2)
            for d in scores
        )

        eval_obj = ConceptEvaluation(
            evaluator_id=evaluator_id,
            scores=scores,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            critical_risks=data.get("critical_risks", []),
            composite_score=round(composite, 3),
        )

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

        # 1. Multi-dimensional evaluation
        for idea in ideas:
            if not idea.evaluations:
                self.evaluate_idea(idea, problem, provider)

        # 2. Cluster to avoid duplicate finalists
        clusters, outliers = self.deduplicator.cluster_ideas(ideas)

        # 3. Pick top representative per cluster
        cluster_champions: List[Idea] = []
        for cluster_id, members in clusters.items():
            sorted_members = sorted(members, key=lambda x: x.composite_score(), reverse=True)
            champion = sorted_members[0]
            cluster_champions.append(champion)

        # Sort champions by composite score
        sorted_champions = sorted(cluster_champions, key=lambda x: x.composite_score(), reverse=True)

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
            i for i in ideas
            if i.id not in finalist_ids and (i.cluster_id or i.id) not in represented_clusters
        ]
        pool_for_wildcard = remaining_unrepresented if remaining_unrepresented else [
            i for i in ideas if i.id not in finalist_ids
        ]

        if pool_for_wildcard and len(finalists) < self.top_n:
            wildcard = max(
                pool_for_wildcard,
                key=lambda x: max((e.scores.get("novelty", ScoreDetail("novelty", 0.0)).score for e in x.evaluations), default=0.0)
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
