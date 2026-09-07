"""Data model for persistent creative search runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import Idea, LineageGraph
from howlcreate.models.operator import AssumptionItem, ReframingLens


@dataclass
class ConvergenceDecision:
    """Rationale for why an idea became a finalist or was set aside."""
    idea_id: str
    status: str  # FINALIST, SET_ASIDE, MERGED
    rationale: str
    strengths_emphasized: List[str] = field(default_factory=list)
    risks_noted: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "idea_id": self.idea_id,
            "status": self.status,
            "rationale": self.rationale,
            "strengths_emphasized": self.strengths_emphasized,
            "risks_noted": self.risks_noted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConvergenceDecision:
        return cls(
            idea_id=data["idea_id"],
            status=data["status"],
            rationale=data["rationale"],
            strengths_emphasized=data.get("strengths_emphasized", []),
            risks_noted=data.get("risks_noted", []),
        )


@dataclass
class RunRecord:
    """Full persistent state of a creative run."""
    run_id: str
    problem: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[AssumptionItem] = field(default_factory=list)
    reframings: List[ReframingLens] = field(default_factory=list)
    graph: LineageGraph = field(default_factory=LineageGraph)
    finalist_ids: List[str] = field(default_factory=list)
    decisions: Dict[str, ConvergenceDecision] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_finalists(self) -> List[Idea]:
        return [self.graph.nodes[fid] for fid in self.finalist_ids if fid in self.graph.nodes]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "problem": self.problem,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "config": self.config,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "reframings": [r.to_dict() for r in self.reframings],
            "graph": self.graph.to_dict(),
            "finalist_ids": self.finalist_ids,
            "decisions": {k: v.to_dict() for k, v in self.decisions.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RunRecord:
        record = cls(
            run_id=data["run_id"],
            problem=data["problem"],
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            completed_at=data.get("completed_at"),
            config=data.get("config", {}),
            assumptions=[AssumptionItem.from_dict(a) for a in data.get("assumptions", [])],
            reframings=[ReframingLens.from_dict(r) for r in data.get("reframings", [])],
            graph=LineageGraph.from_dict(data.get("graph", {})),
            finalist_ids=data.get("finalist_ids", []),
            decisions={k: ConvergenceDecision.from_dict(v) for k, v in data.get("decisions", {}).items()},
            metadata=data.get("metadata", {}),
        )
        return record
