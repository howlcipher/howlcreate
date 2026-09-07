"""Data models for ideas, concept graphs, lineage, and epistemic boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EpistemicStatus(str, Enum):
    """Categorical boundary for claims, ensuring speculation is never conflated with fact."""
    FACT = "FACT"
    ASSUMPTION = "ASSUMPTION"
    SPECULATION = "SPECULATION"
    HYPOTHESIS = "HYPOTHESIS"
    IMAGINED_POSSIBILITY = "IMAGINED_POSSIBILITY"
    ANALOGY = "ANALOGY"
    PREDICTION = "PREDICTION"


class ConceptStatus(str, Enum):
    """Lifecycle state of a concept within the creative search."""
    CANDIDATE = "CANDIDATE"
    MUTATED = "MUTATED"
    COMBINED = "COMBINED"
    CHALLENGED = "CHALLENGED"
    FINALIST = "FINALIST"
    SET_ASIDE = "SET_ASIDE"
    MERGED = "MERGED"


@dataclass
class ScoreDetail:
    """Individual dimension score with rationale and uncertainty."""
    dimension: str
    score: float  # 0.0 to 1.0
    rationale: str = ""
    uncertainty: float = 0.0  # 0.0 (high certainty) to 1.0 (pure guess)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 3),
            "rationale": self.rationale,
            "uncertainty": round(self.uncertainty, 3),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScoreDetail:
        return cls(
            dimension=data["dimension"],
            score=float(data["score"]),
            rationale=data.get("rationale", ""),
            uncertainty=float(data.get("uncertainty", 0.0)),
        )


@dataclass
class ConceptEvaluation:
    """Multi-criteria evaluation for an idea from an evaluator/persona."""
    evaluator_id: str
    scores: Dict[str, ScoreDetail] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    critical_risks: List[str] = field(default_factory=list)
    composite_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluator_id": self.evaluator_id,
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "critical_risks": self.critical_risks,
            "composite_score": round(self.composite_score, 3),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConceptEvaluation:
        scores = {k: ScoreDetail.from_dict(v) for k, v in data.get("scores", {}).items()}
        return cls(
            evaluator_id=data["evaluator_id"],
            scores=scores,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            critical_risks=data.get("critical_risks", []),
            composite_score=float(data.get("composite_score", 0.0)),
        )


@dataclass
class Idea:
    """First-class representation of a creative concept."""
    id: str
    title: str
    description: str
    problem_framing: str = ""
    core_mechanism: str = ""
    operator_used: str = "initial_seed"
    parent_ids: List[str] = field(default_factory=list)
    origin: str = "root"
    epistemic_status: EpistemicStatus = EpistemicStatus.IMAGINED_POSSIBILITY
    assumptions: List[str] = field(default_factory=list)
    changed_assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    analogies: List[str] = field(default_factory=list)
    speculations: List[str] = field(default_factory=list)
    evidence_needs: List[str] = field(default_factory=list)
    unanswered_questions: List[str] = field(default_factory=list)
    criticisms: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    status: ConceptStatus = ConceptStatus.CANDIDATE
    evaluations: List[ConceptEvaluation] = field(default_factory=list)
    cluster_id: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def composite_score(self) -> float:
        """Returns average composite score across all evaluators, if evaluated."""
        if not self.evaluations:
            return 0.0
        return sum(e.composite_score for e in self.evaluations) / len(self.evaluations)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "problem_framing": self.problem_framing,
            "core_mechanism": self.core_mechanism,
            "operator_used": self.operator_used,
            "parent_ids": self.parent_ids,
            "origin": self.origin,
            "epistemic_status": self.epistemic_status.value,
            "assumptions": self.assumptions,
            "changed_assumptions": self.changed_assumptions,
            "constraints": self.constraints,
            "analogies": self.analogies,
            "speculations": self.speculations,
            "evidence_needs": self.evidence_needs,
            "unanswered_questions": self.unanswered_questions,
            "criticisms": self.criticisms,
            "mutations": self.mutations,
            "status": self.status.value,
            "evaluations": [e.to_dict() for e in self.evaluations],
            "cluster_id": self.cluster_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Idea:
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            problem_framing=data.get("problem_framing", ""),
            core_mechanism=data.get("core_mechanism", ""),
            operator_used=data.get("operator_used", "initial_seed"),
            parent_ids=data.get("parent_ids", []),
            origin=data.get("origin", "root"),
            epistemic_status=EpistemicStatus(
                data.get("epistemic_status", EpistemicStatus.IMAGINED_POSSIBILITY.value)
            ),
            assumptions=data.get("assumptions", []),
            changed_assumptions=data.get("changed_assumptions", []),
            constraints=data.get("constraints", []),
            analogies=data.get("analogies", []),
            speculations=data.get("speculations", []),
            evidence_needs=data.get("evidence_needs", []),
            unanswered_questions=data.get("unanswered_questions", []),
            criticisms=data.get("criticisms", []),
            mutations=data.get("mutations", []),
            status=ConceptStatus(data.get("status", ConceptStatus.CANDIDATE.value)),
            evaluations=[ConceptEvaluation.from_dict(e) for e in data.get("evaluations", [])],
            cluster_id=data.get("cluster_id"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class LineageEdge:
    """Directed relationship between parent idea(s) and a derived idea."""
    parent_id: str
    child_id: str
    operator: str
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "operator": self.operator,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LineageEdge:
        return cls(
            parent_id=data["parent_id"],
            child_id=data["child_id"],
            operator=data["operator"],
            rationale=data.get("rationale", ""),
        )


@dataclass
class LineageGraph:
    """DAG of concepts tracking provenance, operations, and concept evolution."""
    nodes: Dict[str, Idea] = field(default_factory=dict)
    edges: List[LineageEdge] = field(default_factory=list)

    def add_idea(self, idea: Idea) -> None:
        """Register an idea in the graph."""
        self.nodes[idea.id] = idea
        for pid in idea.parent_ids:
            if pid in self.nodes:
                self.add_edge(pid, idea.id, idea.operator_used)

    def add_edge(self, parent_id: str, child_id: str, operator: str, rationale: str = "") -> None:
        """Add a directed derivation edge."""
        # Avoid duplicate edges
        for edge in self.edges:
            if edge.parent_id == parent_id and edge.child_id == child_id and edge.operator == operator:
                return
        self.edges.append(LineageEdge(parent_id, child_id, operator, rationale))

    def get_ancestors(self, idea_id: str) -> List[str]:
        """Return all ancestor IDs in topological order."""
        visited: set[str] = set()
        ancestors: List[str] = []

        def _traverse(curr_id: str):
            if curr_id not in self.nodes:
                return
            for edge in self.edges:
                if edge.child_id == curr_id and edge.parent_id not in visited:
                    visited.add(edge.parent_id)
                    ancestors.append(edge.parent_id)
                    _traverse(edge.parent_id)

        _traverse(idea_id)
        return ancestors

    def get_descendants(self, idea_id: str) -> List[str]:
        """Return all descendant IDs."""
        visited: set[str] = set()
        descendants: List[str] = []

        def _traverse(curr_id: str):
            for edge in self.edges:
                if edge.parent_id == curr_id and edge.child_id not in visited:
                    visited.add(edge.child_id)
                    descendants.append(edge.child_id)
                    _traverse(edge.child_id)

        _traverse(idea_id)
        return descendants

    def validate_dag(self) -> bool:
        """Validate that the concept graph contains no cycles."""
        adj: Dict[str, List[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            if edge.parent_id in adj:
                adj[edge.parent_id].append(edge.child_id)

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if _has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in self.nodes:
            if node not in visited:
                if _has_cycle(node):
                    return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LineageGraph:
        graph = cls()
        for k, v in data.get("nodes", {}).items():
            graph.nodes[k] = Idea.from_dict(v)
        for e in data.get("edges", []):
            graph.edges.append(LineageEdge.from_dict(e))
        return graph
