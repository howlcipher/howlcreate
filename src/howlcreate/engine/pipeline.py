"""Master Creative Pipeline orchestrating divergent exploration, mutation, and convergence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import uuid

from howlcreate.engine.convergence import ConvergenceEngine
from howlcreate.engine.dedup import ConceptDeduplicator
from howlcreate.engine.storage import RunStorage
from howlcreate.models.run import RunRecord
from howlcreate.operators.adversarial import AdversarialCritiqueOperator
from howlcreate.operators.analogy import AnalogicalReasoningOperator
from howlcreate.operators.assumptions import AssumptionOperator
from howlcreate.operators.branching import IndependentBranchingOperator
from howlcreate.operators.combination import ForcedCombinationOperator
from howlcreate.operators.constraints import ConstraintMutationOperator
from howlcreate.operators.extremes import ExtremeSolutionsOperator
from howlcreate.operators.reframing import ReframingOperator
from howlcreate.operators.second_order import SecondOrderOperator
from howlcreate.operators.simplification import SimplificationOperator
from howlcreate.operators.substitution import SubstitutionOperator
from howlcreate.operators.synthesis import SynthesisOperator
from howlcreate.providers.base import BaseProvider
from howlcreate.providers.registry import registry


@dataclass
class PipelineConfig:
    """Execution parameters for a creative search run."""
    top_n: int = 3
    similarity_threshold: float = 0.52
    enable_all_operators: bool = True
    provider_name: str = "auto"
    save_run: bool = True
    custom_storage_dir: Optional[Path] = None
    on_step_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None


class CreativePipeline:
    """Orchestrates the divergent-to-convergent creative reasoning lifecycle."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.storage = RunStorage(storage_dir=self.config.custom_storage_dir)
        self.deduplicator = ConceptDeduplicator(similarity_threshold=self.config.similarity_threshold)
        self.convergence_engine = ConvergenceEngine(deduplicator=self.deduplicator, top_n=self.config.top_n)

    def _notify(self, phase: str, payload: Dict[str, Any]) -> None:
        if self.config.on_step_callback:
            self.config.on_step_callback(phase, payload)

    def execute(self, problem: str, provider: Optional[BaseProvider] = None) -> RunRecord:
        """Execute the full creative reasoning run from problem formulation to finalists."""
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        active_provider = provider or registry.get_provider(self.config.provider_name)

        record = RunRecord(
            run_id=run_id,
            problem=problem,
            config={
                "provider": active_provider.model_name,
                "provider_type": type(active_provider).__name__,
                "top_n": self.config.top_n,
                "similarity_threshold": self.config.similarity_threshold,
            },
        )
        graph = record.graph

        self._notify("start", {"run_id": run_id, "problem": problem})

        # -------------------------------------------------------------
        # 1. UNDERSTAND & EXTRACT ASSUMPTIONS (Explicit & Implicit)
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Assumption Extraction & Inversion"})
        asm_op = AssumptionOperator()
        asm_result = asm_op.execute(problem, active_provider)
        record.assumptions = asm_result.assumptions
        for idea in asm_result.ideas:
            graph.add_idea(idea)

        # -------------------------------------------------------------
        # 2. REFRAME (Multiple Perspectives & Lenses)
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Reframing via Stakeholder Lenses"})
        reframe_op = ReframingOperator()
        reframe_result = reframe_op.execute(problem, active_provider)
        record.reframings = reframe_result.reframings
        for idea in reframe_result.ideas:
            graph.add_idea(idea)

        # -------------------------------------------------------------
        # 3. DIVERGE (Independent Branching to Avoid Anchoring)
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Independent Branching (Multi-Archetype)"})
        explorer_a = IndependentBranchingOperator(branch_archetype="Structural Architect")
        res_a = explorer_a.execute(problem, active_provider, parameters={"focus_domain": "decentralized protocols"})
        for idea in res_a.ideas:
            graph.add_idea(idea)

        explorer_b = IndependentBranchingOperator(branch_archetype="Incentive & Micro-Economy Designer")
        res_b = explorer_b.execute(problem, active_provider, parameters={"focus_domain": "mechanism design & game theory"})
        for idea in res_b.ideas:
            graph.add_idea(idea)

        # -------------------------------------------------------------
        # 4. MUTATE (Constraints, Analogies, Extremes, Substitutions)
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Lateral Mutation & Domain Analogies"})
        pool_snapshot = list(graph.nodes.values())

        # Constraint Mutation
        mut_op = ConstraintMutationOperator()
        mut_res = mut_op.execute(problem, active_provider, context_ideas=pool_snapshot)
        for idea in mut_res.ideas:
            graph.add_idea(idea)

        # Analogical Reasoning (Biology, Logistics, etc.)
        analogy_op = AnalogicalReasoningOperator()
        analogy_res = analogy_op.execute(problem, active_provider, context_ideas=pool_snapshot)
        for idea in analogy_res.ideas:
            graph.add_idea(idea)

        if self.config.enable_all_operators:
            # Extreme Solutions
            extreme_op = ExtremeSolutionsOperator()
            ext_res = extreme_op.execute(problem, active_provider, context_ideas=pool_snapshot)
            for idea in ext_res.ideas:
                graph.add_idea(idea)

            # Simplification (Problem Dissolution)
            simp_op = SimplificationOperator()
            simp_res = simp_op.execute(problem, active_provider, context_ideas=pool_snapshot)
            for idea in simp_res.ideas:
                graph.add_idea(idea)

            # Substitution
            sub_op = SubstitutionOperator()
            sub_res = sub_op.execute(problem, active_provider, context_ideas=pool_snapshot)
            for idea in sub_res.ideas:
                graph.add_idea(idea)

        # -------------------------------------------------------------
        # 5. CROSS-POLLINATE & COMBINE (Forced Combination)
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Forced Combinations & Cross-Pollination"})
        current_ideas = list(graph.nodes.values())
        if len(current_ideas) >= 2:
            combo_op = ForcedCombinationOperator()
            combo_res = combo_op.execute(problem, active_provider, context_ideas=current_ideas)
            for idea in combo_res.ideas:
                graph.add_idea(idea)

        # -------------------------------------------------------------
        # 6. ADVERSARIAL CRITIQUE & DEFENSIVE HARDENING
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Adversarial Critique & Brittleness Hardening"})
        if graph.nodes:
            adv_op = AdversarialCritiqueOperator()
            # Attack the most prominent or first branch
            adv_target = list(graph.nodes.values())[0]
            adv_res = adv_op.execute(problem, active_provider, context_ideas=[adv_target])
            for idea in adv_res.ideas:
                graph.add_idea(idea)

        # -------------------------------------------------------------
        # 7. SECOND-ORDER EXPLORATION
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Second-Order Ripple Effect Exploration"})
        sec_op = SecondOrderOperator()
        sec_res = sec_op.execute(problem, active_provider, context_ideas=list(graph.nodes.values())[:1])
        for idea in sec_res.ideas:
            graph.add_idea(idea)

        # -------------------------------------------------------------
        # 8. SYNTHESIS
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Architectural Synthesis of Best Components"})
        synth_op = SynthesisOperator()
        synth_res = synth_op.execute(problem, active_provider, context_ideas=list(graph.nodes.values()))
        for idea in synth_res.ideas:
            graph.add_idea(idea)

        # -------------------------------------------------------------
        # 9. MULTI-DIMENSIONAL EVALUATION & CONVERGENCE
        # -------------------------------------------------------------
        self._notify("phase", {"name": "Multi-Dimensional Evaluation & Diversity-Preserving Convergence"})
        all_ideas = list(graph.nodes.values())
        finalists, decisions = self.convergence_engine.converge(all_ideas, problem, active_provider)

        record.finalist_ids = [f.id for f in finalists]
        record.decisions = decisions
        record.completed_at = datetime.now(timezone.utc).isoformat()

        # -------------------------------------------------------------
        # 10. PERSISTENCE
        # -------------------------------------------------------------
        if self.config.save_run:
            saved_path = self.storage.save_run(record)
            record.metadata["storage_path"] = str(saved_path)

        self._notify("complete", {
            "run_id": run_id,
            "total_concepts_explored": len(all_ideas),
            "finalists_selected": len(finalists),
        })

        return record
