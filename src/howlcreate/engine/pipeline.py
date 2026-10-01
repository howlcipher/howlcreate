"""Master Creative Pipeline orchestrating divergent exploration, mutation, and convergence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
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
from howlcreate.providers.runtime import TrackedProvider
from howl_provider_core import BudgetExceeded, CallBudget, ProviderError


@dataclass
class PipelineConfig:
    """Execution parameters for a creative search run."""

    top_n: int = 3
    similarity_threshold: float = 0.52
    enable_all_operators: bool = True
    provider_name: str = "auto"
    ecosystem_fit_weight: float = 0.0
    max_calls: int = 32
    save_run: bool = True
    custom_storage_dir: Optional[Path] = None
    hard_constraints: Optional[List[str]] = None
    on_step_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None


class CreativePipeline:
    """Orchestrates the divergent-to-convergent creative reasoning lifecycle."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.storage = RunStorage(storage_dir=self.config.custom_storage_dir)
        self.deduplicator = ConceptDeduplicator(
            similarity_threshold=self.config.similarity_threshold
        )
        self.convergence_engine = ConvergenceEngine(
            deduplicator=self.deduplicator,
            top_n=self.config.top_n,
            ecosystem_fit_weight=self.config.ecosystem_fit_weight,
            hard_constraints=self.config.hard_constraints,
        )

    def _notify(self, phase: str, payload: Dict[str, Any]) -> None:
        if self.config.on_step_callback:
            self.config.on_step_callback(phase, payload)

    def execute(self, problem: str, provider: Optional[BaseProvider] = None) -> RunRecord:
        """Execute the full creative reasoning run from problem formulation to finalists."""
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        budget = CallBudget(self.config.max_calls)
        active_provider = TrackedProvider(
            provider or registry.get_provider(self.config.provider_name),
            budget,
            requested=self.config.provider_name
            if provider is None
            else getattr(provider, "requested_provider", type(provider).__name__),
        )

        record = RunRecord(
            run_id=run_id,
            problem=problem,
            config={
                "provider": active_provider.model_name,
                "provider_type": type(active_provider.provider).__name__,
                "requested_provider": active_provider.requested,
                "requested_model": active_provider.model_name,
                "top_n": self.config.top_n,
                "similarity_threshold": self.config.similarity_threshold,
            },
        )
        graph = record.graph

        self._notify("start", {"run_id": run_id, "problem": problem})

        try:
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
            explorer_a = IndependentBranchingOperator(
                branch_archetype="Structure and Failure Boundaries"
            )
            res_a = explorer_a.execute(
                problem, active_provider, parameters={"focus_domain": problem}
            )
            for idea in res_a.ideas:
                graph.add_idea(idea)

            explorer_b = IndependentBranchingOperator(
                branch_archetype="Stakeholder Needs and Resource Tradeoffs"
            )
            res_b = explorer_b.execute(
                problem, active_provider, parameters={"focus_domain": problem}
            )
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
            sec_res = sec_op.execute(
                problem, active_provider, context_ideas=list(graph.nodes.values())[:1]
            )
            for idea in sec_res.ideas:
                graph.add_idea(idea)

            # -------------------------------------------------------------
            # 8. SYNTHESIS
            # -------------------------------------------------------------
            self._notify("phase", {"name": "Architectural Synthesis of Best Components"})
            synth_op = SynthesisOperator()
            synth_res = synth_op.execute(
                problem, active_provider, context_ideas=list(graph.nodes.values())
            )
            for idea in synth_res.ideas:
                graph.add_idea(idea)

            # -------------------------------------------------------------
            # 9. MULTI-DIMENSIONAL EVALUATION & CONVERGENCE
            # -------------------------------------------------------------
            self._notify(
                "phase", {"name": "Multi-Dimensional Evaluation & Diversity-Preserving Convergence"}
            )
            all_ideas = list(graph.nodes.values())
            if not all_ideas:
                record.metadata["status"] = "INVALID_PROVIDER_OUTPUT"
                record.metadata["stop_reason"] = "ZERO_CONCEPTS_GENERATED"
            else:
                finalists, decisions = self.convergence_engine.converge(
                    all_ideas,
                    problem,
                    active_provider,
                    hard_constraints=self.config.hard_constraints,
                )
                record.finalist_ids = [f.id for f in finalists]
                record.decisions = decisions
                if not finalists:
                    record.metadata["status"] = "NO_VIABLE_CANDIDATES"
                    record.metadata["stop_reason"] = "NO_VIABLE_CANDIDATES"
                else:
                    record.metadata["status"] = "COMPLETE"
            record.completed_at = datetime.now(timezone.utc).isoformat()
        except BudgetExceeded:
            record.metadata.update(status="PARTIAL", stop_reason="BUDGET_EXHAUSTED")
        except (ProviderError, RuntimeError, ValueError) as error:
            record.metadata.update(
                status="PARTIAL", stop_reason="PROVIDER_FAILURE", error_type=type(error).__name__
            )
        finally:
            record.completed_at = datetime.now(timezone.utc).isoformat()
            record.metadata.update(
                call_count=budget.calls,
                executions=active_provider.executions,
                call_events=budget.events,
            )
            if self.config.save_run:
                saved_path = self.storage.save_run(record)
                record.metadata["storage_path"] = str(saved_path)
            self._notify(
                "complete",
                {
                    "run_id": run_id,
                    "total_concepts_explored": len(graph.nodes),
                    "finalists_selected": len(record.finalist_ids),
                    "status": record.metadata["status"],
                },
            )

        return record
