"""Data models for creative operators, assumptions, and reframing lenses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List
from howlcreate.models.idea import Idea


class OperatorType(str, Enum):
    """Categorical enumeration of all available creative operators."""
    ASSUMPTION_EXTRACTION = "assumption_extraction"
    ASSUMPTION_INVERSION = "assumption_inversion"
    REFRAMING = "reframing"
    CONSTRAINT_MUTATION = "constraint_mutation"
    ANALOGICAL_REASONING = "analogical_reasoning"
    INDEPENDENT_BRANCHING = "independent_branching"
    FORCED_COMBINATION = "forced_combination"
    ADVERSARIAL_CRITIQUE = "adversarial_critique"
    SECOND_ORDER_EXPLORATION = "second_order_exploration"
    EXTREME_SOLUTIONS = "extreme_solutions"
    SIMPLIFICATION = "simplification"
    SUBSTITUTION = "substitution"
    SYNTHESIS = "synthesis"


@dataclass
class AssumptionItem:
    """An explicit or implicit assumption underlying the problem."""
    id: str
    statement: str
    is_implicit: bool = True
    inversions: List[str] = field(default_factory=list)
    vulnerability: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "is_implicit": self.is_implicit,
            "inversions": self.inversions,
            "vulnerability": self.vulnerability,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AssumptionItem:
        return cls(
            id=data["id"],
            statement=data["statement"],
            is_implicit=data.get("is_implicit", True),
            inversions=data.get("inversions", []),
            vulnerability=data.get("vulnerability", ""),
        )


@dataclass
class ReframingLens:
    """A specific perspective or lens through which a problem is reconsidered."""
    lens_id: str
    perspective: str
    reframed_question: str
    core_focus: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lens_id": self.lens_id,
            "perspective": self.perspective,
            "reframed_question": self.reframed_question,
            "core_focus": self.core_focus,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReframingLens:
        return cls(
            lens_id=data["lens_id"],
            perspective=data["perspective"],
            reframed_question=data["reframed_question"],
            core_focus=data["core_focus"],
        )


@dataclass
class OperatorResult:
    """The structured output produced by a creative operator."""
    operator_type: OperatorType
    ideas: List[Idea] = field(default_factory=list)
    assumptions: List[AssumptionItem] = field(default_factory=list)
    reframings: List[ReframingLens] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
