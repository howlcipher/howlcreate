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
    repair_attempts: int = 1
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
        record = RunRecord(run_id=f"run-{uuid.uuid4().hex[:8]}", problem=problem)
        record.config = {
            "provider_name": self.config.provider_name,
            "top_n": self.config.top_n,
            "similarity_threshold": self.config.similarity_threshold,
            "enable_all_operators": self.config.enable_all_operators,
            "ecosystem_fit_weight": self.config.ecosystem_fit_weight,
            "max_calls": self.config.max_calls,
            "repair_attempts": self.config.repair_attempts,
            "hard_constraints": self.config.hard_constraints,
        }
        record.metadata.update(
            checkpoint_schema="howlcreate.checkpoint/v1",
            completed_phases=[],
            phase_failures=[],
            status="RUNNING",
        )
        return self._continue(record, provider)

    def resume(self, run_id_or_path: str, provider: Optional[BaseProvider] = None) -> RunRecord:
        """Resume only compatible checkpoints; never discover executable provider config."""
        record = self.storage.load_run(run_id_or_path)
        if record.metadata.get("checkpoint_schema") != "howlcreate.checkpoint/v1":
            raise ValueError("incompatible checkpoint schema; only checkpoint/v1 can resume")
        import re

        if not re.fullmatch(r"run-[a-f0-9]{8}", record.run_id):
            raise ValueError("invalid checkpoint run ID")
        if not isinstance(record.metadata.get("completed_phases"), list):
            raise ValueError("invalid checkpoint phase state")
        if not record.graph.validate_dag():
            raise ValueError("invalid checkpoint graph")
        if record.metadata.get("status") == "COMPLETE":
            return record
        for key, value in record.config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.convergence_engine = ConvergenceEngine(
            deduplicator=ConceptDeduplicator(self.config.similarity_threshold),
            top_n=self.config.top_n,
            ecosystem_fit_weight=self.config.ecosystem_fit_weight,
            hard_constraints=self.config.hard_constraints,
        )
        record.metadata.setdefault("resume_history", []).append(
            {
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "prior_call_count": record.metadata.get("call_count", 0),
                "prior_status": record.metadata.get("status"),
                "prior_stop_reason": record.metadata.get("stop_reason"),
                "prior_failed_phase": record.metadata.get("failed_phase"),
            }
        )
        return self._continue(record, provider)

    def _continue(self, record, provider):
        budget = CallBudget(
            self.config.max_calls,
            calls=record.metadata.get("call_count", 0),
            events=list(record.metadata.get("call_events", [])),
        )
        active = TrackedProvider(
            provider or registry.get_provider(self.config.provider_name),
            budget,
            requested=self.config.provider_name
            if provider is None
            else getattr(provider, "requested_provider", type(provider).__name__),
            repair_attempts=self.config.repair_attempts,
        )
        actual_identity = {
            "provider_type": type(active.provider).__name__,
            "requested_provider": active.requested,
            "requested_model": active.model_name,
        }
        if record.config.get("provider_type") and any(
            record.config.get(k) != v for k, v in actual_identity.items()
        ):
            raise ValueError("resume provider identity differs from checkpoint")
        if hasattr(active.provider, "adapter"):
            import hashlib
            from dataclasses import asdict
            import json

            profile = getattr(active.provider.adapter, "config", None)
            if profile is not None:
                signature = hashlib.sha256(
                    json.dumps(asdict(profile), sort_keys=True).encode()
                ).hexdigest()
                if record.config.get("command_profile_hash", signature) != signature:
                    raise ValueError("resume command profile differs from checkpoint")
                record.config["command_profile_hash"] = signature
                record.config["command_timeout_seconds"] = profile.timeout_seconds
                record.config["command_adapter"] = profile.adapter or profile.output_format
        record.config.update(actual_identity)
        prior_executions = list(record.metadata.get("executions", []))
        graph = record.graph
        completed = record.metadata["completed_phases"]
        failures = record.metadata["phase_failures"]
        phase = "start"

        def checkpoint():
            record.metadata.update(
                call_count=budget.calls,
                call_events=budget.events,
                executions=prior_executions + active.executions,
            )
            if self.config.save_run:
                record.metadata["storage_path"] = str(self.storage.save_run(record))

        steps = [
            ("assumptions", AssumptionOperator(), "none"),
            ("reframing", ReframingOperator(), "none"),
            (
                "branch_structure",
                IndependentBranchingOperator(branch_archetype="Structure and Failure Boundaries"),
                "none",
            ),
            (
                "branch_stakeholders",
                IndependentBranchingOperator(
                    branch_archetype="Stakeholder Needs and Resource Tradeoffs"
                ),
                "none",
            ),
            ("mutation", ConstraintMutationOperator(), "mutation"),
            ("analogy", AnalogicalReasoningOperator(), "mutation"),
        ]
        if self.config.enable_all_operators:
            steps.extend(
                [
                    ("extremes", ExtremeSolutionsOperator(), "mutation"),
                    ("simplification", SimplificationOperator(), "mutation"),
                    ("substitution", SubstitutionOperator(), "mutation"),
                ]
            )
        steps.extend(
            [
                ("combination", ForcedCombinationOperator(), "all"),
                ("adversarial", AdversarialCritiqueOperator(), "first"),
                ("second_order", SecondOrderOperator(), "first"),
                ("synthesis", SynthesisOperator(), "all"),
            ]
        )
        phase_order = [name for name, _, _ in steps] + ["convergence"]
        if completed != phase_order[: len(completed)]:
            raise ValueError("checkpoint completed phases are not a compatible ordered prefix")
        if len(budget.events) != budget.calls:
            raise ValueError("checkpoint budget history is inconsistent")
        # Persist the original mutation context IDs, so resume does not change its seed pool.
        record.metadata.update(status="RUNNING")
        if record.finalist_ids:
            record.metadata["retained_finalists_from_checkpoint"] = True
        checkpoint()
        can_converge = True
        try:
            for phase, operator, context_kind in steps:
                if phase in completed:
                    continue
                self._notify("phase", {"name": phase})
                pool = list(graph.nodes.values())
                if context_kind == "mutation":
                    ids = record.metadata.setdefault("mutation_seed_ids", list(graph.nodes))
                    pool = [graph.nodes[i] for i in ids]
                elif context_kind == "first":
                    pool = pool[:1]
                elif context_kind == "none":
                    pool = []
                try:
                    result = operator.execute(record.problem, active, context_ideas=pool)
                except (ProviderError, RuntimeError, ValueError) as error:
                    failure = getattr(error, "failure", None) or {
                        "category": "INVALID_PROVIDER_OUTPUT",
                        "recovery": "REPAIRABLE",
                        "sanitized_message": "phase output failed validation",
                    }
                    failures.append(
                        {"phase": phase, "call_count": budget.calls, "failure": failure}
                    )
                    record.metadata.update(
                        failed_phase=phase,
                        status="PARTIAL",
                        stop_reason="BUDGET_EXHAUSTED"
                        if isinstance(error, BudgetExceeded)
                        else "PROVIDER_FAILURE",
                        error_type=type(error).__name__,
                    )
                    # Optional later phases can fail without erasing the valid pool. Never
                    # dispatch more calls after budget, authentication, quota or cancellation.
                    can_converge = (
                        phase
                        not in {
                            "assumptions",
                            "reframing",
                            "branch_structure",
                            "branch_stakeholders",
                        }
                        and failure["recovery"] == "REPAIRABLE"
                    )
                    checkpoint()
                    break
                for idea in result.ideas:
                    graph.add_idea(idea)
                if phase == "assumptions":
                    record.assumptions = result.assumptions
                if phase == "reframing":
                    record.reframings = result.reframings
                completed.append(phase)
                if record.metadata.get("failed_phase") == phase:
                    record.metadata.pop("failed_phase")
                checkpoint()
            phase = "convergence"
            if graph.nodes and can_converge:
                self._notify("phase", {"name": phase})
                checkpoint()
                finalists, decisions = self.convergence_engine.converge(
                    list(graph.nodes.values()),
                    record.problem,
                    active,
                    hard_constraints=self.config.hard_constraints,
                    allow_partial=True,
                )
                for failure in self.convergence_engine.last_failures:
                    failures.append({"phase": "convergence", "failure": failure})
                    record.metadata.update(
                        failed_phase="convergence",
                        stop_reason=(
                            "BUDGET_EXHAUSTED"
                            if failure["category"] == "BUDGET_EXHAUSTED"
                            else record.metadata.get("stop_reason", "PROVIDER_FAILURE")
                        ),
                    )
                record.finalist_ids = [idea.id for idea in finalists]
                record.metadata["retained_finalists_from_checkpoint"] = False
                record.decisions = decisions
                record.metadata["status"] = (
                    "PARTIAL" if failures else ("COMPLETE" if finalists else "NO_VIABLE_CANDIDATES")
                )
                if record.metadata["status"] == "COMPLETE":
                    for key in ("stop_reason", "error_type", "failed_phase"):
                        record.metadata.pop(key, None)
                if not failures and not finalists:
                    record.metadata["stop_reason"] = "NO_VIABLE_CANDIDATES"
                if not failures:
                    completed.append(phase)
            elif not graph.nodes and not failures:
                record.metadata.update(
                    status="INVALID_PROVIDER_OUTPUT", stop_reason="ZERO_CONCEPTS_GENERATED"
                )
        except (ProviderError, RuntimeError, ValueError) as error:
            failures.append(
                {
                    "phase": phase,
                    "failure": getattr(error, "failure", None)
                    or {
                        "category": "INVALID_PROVIDER_OUTPUT",
                        "sanitized_message": "phase output failed validation",
                    },
                }
            )
            record.metadata.update(
                status="PARTIAL",
                failed_phase=phase,
                stop_reason="BUDGET_EXHAUSTED"
                if isinstance(error, BudgetExceeded)
                else "PROVIDER_FAILURE",
                error_type=type(error).__name__,
            )
        except BaseException:
            record.metadata.update(status="PARTIAL", failed_phase=phase, stop_reason="INTERRUPTED")
            raise
        finally:
            record.completed_at = datetime.now(timezone.utc).isoformat()
            if failures and record.metadata["status"] == "RUNNING":
                record.metadata["status"] = "PARTIAL"
            record.metadata["completion_detail"] = (
                ("PARTIAL_WITH_FINALISTS" if record.finalist_ids else "PARTIAL_NO_FINALISTS")
                if record.metadata["status"] == "PARTIAL"
                else record.metadata["status"]
            )
            checkpoint()
        self._notify(
            "complete",
            {
                "run_id": record.run_id,
                "total_concepts_explored": len(graph.nodes),
                "finalists_selected": len(record.finalist_ids),
                "status": record.metadata["status"],
            },
        )
        return record
