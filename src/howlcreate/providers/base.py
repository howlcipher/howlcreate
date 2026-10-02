"""Abstract base class and response schemas for LLM and heuristic providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, Optional
from howl_provider_core import ProviderError


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProviderError("duplicate JSON response key")
        result[key] = value
    return result


@dataclass
class ProviderResponse:
    """Standardized response from any model provider."""

    content: str
    model: str
    provider: str
    structured_data: Optional[Dict[str, Any]] = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
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
                data = json.loads(candidate, object_pairs_hook=_unique_keys)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        # Try parsing full text or outer curly braces
        curly_match = re.search(r"(\{[\s\S]*\})", text)
        if curly_match:
            candidate = curly_match.group(1).strip()
            try:
                data = json.loads(candidate, object_pairs_hook=_unique_keys)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        try:
            data = json.loads(text, object_pairs_hook=_unique_keys)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        return None


class BaseProvider(ABC):
    """Abstract interface for all model and inference backends."""

    sampling_capabilities = {"temperature": False, "seed": False, "top_p": False}

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name

    def generate_for(self, operation: str, prompt: str, **kwargs) -> ProviderResponse:
        """Explicit operation identity; legacy adapters need only implement generate."""
        response = self.generate(prompt, **kwargs)
        try:
            if kwargs.get("json_mode") and response.extract_json() is None:
                raise ProviderError("provider returned malformed structured output")
        except ProviderError as error:
            error.response = response
            raise
        return response

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
