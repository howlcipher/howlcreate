"""Base class for all creative operators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from howlcreate.models.idea import Idea
from howlcreate.models.operator import OperatorResult, OperatorType
from howlcreate.providers.base import BaseProvider


class BaseOperator(ABC):
    """Abstract base class for creative operators."""

    def __init__(self, operator_type: OperatorType, name: Optional[str] = None):
        self.operator_type = operator_type
        self.name = name or operator_type.value

    @abstractmethod
    def execute(
        self,
        problem: str,
        provider: BaseProvider,
        context_ideas: Optional[List[Idea]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperatorResult:
        """Execute the creative operator on the problem and optional context."""
        pass
