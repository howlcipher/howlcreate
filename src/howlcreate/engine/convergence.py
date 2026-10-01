"""Multi-dimensional evaluation, uncertainty tracking, and convergence engine."""

from __future__ import annotations

import json
import math
import re

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
        hard_constraints: Optional[List[str]] = None,
    ):
        self.deduplicator = deduplicator or ConceptDeduplicator()
        self.top_n = top_n
        self.hard_constraints = list(hard_constraints) if hard_constraints else []
        if not 0 <= ecosystem_fit_weight <= 1:
            raise ValueError("ecosystem_fit_weight must be between zero and one")
        self.dimensions = list(self.DEFAULT_DIMENSIONS)
        self.weights = {
            key: value * (1 - ecosystem_fit_weight) for key, value in self.DIMENSION_WEIGHTS.items()
        }
        if ecosystem_fit_weight:
            self.dimensions.append("ecosystem_fit")
            self.weights["ecosystem_fit"] = ecosystem_fit_weight

    def evaluate_hard_constraints(self, idea: Idea, hard_constraints: List[str]) -> List[str]:
        """Determine if an idea violates any mandatory hard constraint.

        Mandatory constraints include:
        - Negative prohibitions: 'no ...', 'zero ...', 'do not use ...', 'do not ...',
          'never ...', 'must not ...', 'cannot ...', 'must run without ...'
        - Positive requirements: 'must have ...', 'must include ...', 'must support ...',
          'must use ...', 'requires ...', 'mandatory: ...'

        Soft preferences ('prefer ...', 'preferred', 'avoid ... when practical', 'optional',
        'acceptable') are recognized as non-gating and do not disqualify candidates at the hard gate.
        """
        violations: List[str] = []
        if hasattr(idea, "constraints_violated") and idea.constraints_violated:
            violations.extend(idea.constraints_violated)
        if idea.provenance.get("hard_constraint_violations"):
            violations.extend(idea.provenance["hard_constraint_violations"])

        combined_text = f"{idea.title} {idea.description} {idea.core_mechanism}".lower()
        criticisms_text = " ".join(idea.criticisms).lower()

        preference_markers = [
            "prefer ",
            "preferred",
            "is preferred",
            "acceptable",
            "when practical",
            "where practical",
            "optional",
            "nice to have",
        ]

        def _is_negated_or_compliant(text: str, term: str) -> bool:
            """Check if occurrences of term in text appear in a negated/compliant context."""
            patterns = [
                rf"\bwithout\s+(?:using\s+)?{re.escape(term)}\b",
                rf"\bno\s+(?:reliance\s+on\s+)?{re.escape(term)}\b",
                rf"\bzero\s+{re.escape(term)}\b",
                rf"\bnever\s+(?:persist\s+|use\s+|store\s+|rely\s+on\s+)?{re.escape(term)}\b",
                rf"\bdo\s+not\s+(?:use\s+|persist\s+|rely\s+on\s+)?{re.escape(term)}\b",
                rf"\bdoes\s+not\s+(?:use\s+|require\s+|need\s+|persist\s+|rely\s+on\s+)?{re.escape(term)}\b",
                rf"\bnot\s+(?:using\s+|persisting\s+|requiring\s+)?{re.escape(term)}\b",
                rf"\beliminat(?:es|ing)\s+(?:the\s+need\s+for\s+)?{re.escape(term)}\b",
                rf"\bfree\s+from\s+{re.escape(term)}\b",
                rf"\bavoid(?:s|ing)?\s+{re.escape(term)}\b",
            ]
            for pat in patterns:
                if re.search(pat, text):
                    return True
            return False

        for hc in hard_constraints:
            hc_lower = hc.lower().strip()
            # 1. Skip soft preferences that are not mandatory prohibitions or requirements
            if any(pm in hc_lower for pm in preference_markers) and not any(
                hc_lower.startswith(m) for m in ["must ", "never ", "cannot ", "mandatory:"]
            ):
                continue

            # 2. Explicit violation markers in criticisms or text
            if (
                f"violates {hc_lower}" in criticisms_text
                or f"violates: {hc_lower}" in criticisms_text
                or f"fails {hc_lower}" in criticisms_text
                or f"violates {hc_lower}" in combined_text
                or f"violates: {hc_lower}" in combined_text
            ):
                violations.append(f"Constraint violation: {hc}")
                continue

            # 3. Negative prohibitions
            neg_match = None
            neg_prefixes = [
                (r"^(?:no|zero)\s+", ""),
                (r"^(?:do\s+not\s+use|do\s+not)\s+", ""),
                (r"^never\s+(?:use\s+|persist\s+)?", ""),
                (r"^(?:must\s+not\s+use|must\s+not|cannot\s+use|cannot)\s+", ""),
                (r"^must\s+run\s+without\s+", ""),
            ]
            for pat, repl in neg_prefixes:
                m = re.match(pat, hc_lower)
                if m:
                    neg_match = re.sub(pat, repl, hc_lower).strip().rstrip(".")
                    break

            if neg_match:
                forbidden = neg_match
                base_forbidden = re.sub(
                    r"\b(reliance|usage|dependency|dependencies)\b", "", forbidden
                ).strip()
                terms_to_check = [forbidden]
                if base_forbidden and base_forbidden != forbidden:
                    terms_to_check.append(base_forbidden)
                    terms_to_check.append(base_forbidden.replace("-", " "))
                    terms_to_check.append(base_forbidden.replace(" ", "-"))

                matched_term = None
                for term in terms_to_check:
                    if term and term in combined_text:
                        if not _is_negated_or_compliant(combined_text, term):
                            matched_term = term
                            break
                if matched_term:
                    violations.append(f"Requires prohibited mechanism: {hc}")
                continue

            # 4. Positive requirements
            pos_match = None
            pos_prefixes = [
                r"^(?:must\s+have|must\s+include|must\s+support|must\s+use|requires)\s+",
                r"^(?:mandatory:|require:)\s*",
            ]
            for pat in pos_prefixes:
                m = re.match(pat, hc_lower)
                if m:
                    pos_match = re.sub(pat, "", hc_lower).strip().rstrip(".")
                    break

            if pos_match:
                required = pos_match
                if required and required not in combined_text:
                    violations.append(f"Missing mandatory requirement: {hc}")

        return list(dict.fromkeys(violations))

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
        hard_constraints: Optional[List[str]] = None,
    ) -> Tuple[List[Idea], Dict[str, ConvergenceDecision]]:
        """Evaluate all ideas, gate by hard constraints, cluster by similarity, and select diverse finalists."""
        if not ideas:
            return [], {}

        active_constraints = (
            list(hard_constraints) if hard_constraints is not None else list(self.hard_constraints)
        )

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
            constraint_prompt = (
                f"\nMandatory Hard Constraints: {json.dumps(active_constraints)}\n"
                if active_constraints
                else ""
            )
            prompt = (
                f'Problem: "{problem}"\n'
                f"{constraint_prompt}"
                "Evaluate each candidate against the supplied objective and constraints, not ecosystem membership. "
                'Return {"evaluations": {candidate_id: {"scores": {dimension: '
                '{"score": number, "uncertainty": number, "rationale": string}}, '
                '"strengths": [], "weaknesses": [], "critical_risks": [], "constraint_violations": []}}}. '
                "Scores and uncertainty must be between 0 and 1. Dimensions: "
                + ", ".join(self.dimensions)
                + ". strategic_fit means alignment with this user's objective and constraints. "
                "novelty means difference from conventional approaches; feasibility means "
                "implementability; usefulness means user value; simplicity means minimal complexity. "
                "List any violated mandatory hard constraints under constraint_violations. "
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
                    reported_violations = value.get("constraint_violations", [])
                    if isinstance(reported_violations, list) and reported_violations:
                        idea.provenance.setdefault("hard_constraint_violations", []).extend(
                            reported_violations
                        )
                except (KeyError, TypeError, ValueError):
                    errors.append("incomplete evaluation")
        if errors:
            raise ValueError("incomplete batch evaluation; valid scores retained, none fabricated")

        # 2. Hard constraint evaluation: partition ideas into eligible and ineligible
        for idea in ideas:
            violations = self.evaluate_hard_constraints(idea, active_constraints)
            if violations:
                idea.provenance["hard_constraint_violations"] = violations

        eligible_ideas = [
            idea for idea in ideas if not idea.provenance.get("hard_constraint_violations")
        ]
        ineligible_ideas = [
            idea for idea in ideas if idea.provenance.get("hard_constraint_violations")
        ]

        decisions: Dict[str, ConvergenceDecision] = {}

        # If no eligible ideas exist, all candidates violated hard constraints
        if not eligible_ideas:
            for idea in ideas:
                idea.status = ConceptStatus.SET_ASIDE
                violations = idea.provenance.get(
                    "hard_constraint_violations", ["Hard constraint violation"]
                )
                score = idea.composite_score()
                decisions[idea.id] = ConvergenceDecision(
                    idea_id=idea.id,
                    status=ConceptStatus.SET_ASIDE.value,
                    rationale=(
                        f"Disqualified by hard constraint violation (score: {score:.2f}): "
                        f"{'; '.join(violations)}. Candidate preserved as rejected evidence."
                    ),
                    risks_noted=violations,
                )
            return [], decisions

        # 3. Cluster eligible ideas to avoid duplicate finalists
        clusters, _outliers = self.deduplicator.cluster_ideas(eligible_ideas)

        # 4. Pick top representative per cluster from eligible ideas only
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

        # Look for high-novelty wildcard from unrepresented clusters/outliers (ELIGIBLE ONLY)
        remaining_unrepresented = [
            i
            for i in eligible_ideas
            if i.id not in finalist_ids and (i.cluster_id or i.id) not in represented_clusters
        ]
        pool_for_wildcard = (
            remaining_unrepresented
            if remaining_unrepresented
            else [i for i in eligible_ideas if i.id not in finalist_ids]
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

        # 5. Formulate convergence decisions with inspectable rationale
        # First record ineligible candidates as set aside due to hard constraint violations
        for idea in ineligible_ideas:
            idea.status = ConceptStatus.SET_ASIDE
            violations = idea.provenance.get("hard_constraint_violations", [])
            score = idea.composite_score()
            decisions[idea.id] = ConvergenceDecision(
                idea_id=idea.id,
                status=ConceptStatus.SET_ASIDE.value,
                rationale=(
                    f"Disqualified by hard constraint violation (score: {score:.2f}): "
                    f"{'; '.join(violations)}. Candidate preserved as rejected evidence."
                ),
                risks_noted=violations,
            )

        # Then record eligible candidates
        for idea in eligible_ideas:
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
                        f"with superior balance of novelty and feasibility, satisfying all hard constraints."
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
