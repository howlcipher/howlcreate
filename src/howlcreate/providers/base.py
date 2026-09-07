"""Abstract base class and response schemas for LLM and heuristic providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, Optional


@dataclass
class ProviderResponse:
    """Standardized response from any model provider."""
    content: str
    model: str
    provider: str
    structured_data: Optional[Dict[str, Any]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def extract_json(self) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from model output, handling code fences and preamble."""
        if self.structured_data:
            return self.structured_data

        text = self.content.strip()
        # Look for markdown code fence ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            candidate = fence_match.group(1).strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        # Try parsing full text or outer curly braces
        curly_match = re.search(r"(\{[\s\S]*\})", text)
        if curly_match:
            candidate = curly_match.group(1).strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        return None


class BaseProvider(ABC):
    """Abstract interface for all model and inference backends."""

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ProviderResponse:
        """Generate a response for the prompt."""
        pass
