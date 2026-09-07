"""Provider registry and role-based multi-agent routing."""

from __future__ import annotations

from typing import Dict
from howlcreate.providers.base import BaseProvider
from howlcreate.providers.deterministic import DeterministicProvider
from howlcreate.providers.ollama import OllamaProvider
from howlcreate.providers.openai_compatible import OpenAICompatibleProvider


class ProviderRegistry:
    """Registry maintaining available providers and role-to-provider mappings."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {
            "deterministic": DeterministicProvider(),
        }
        self._role_mappings: Dict[str, str] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def assign_role(self, role: str, provider_name: str) -> None:
        self._role_mappings[role] = provider_name

    def get_provider(self, name_or_role: str = "auto") -> BaseProvider:
        """Resolve a provider by explicit name, assigned role, or auto-detection."""
        # 1. Check if assigned as a role
        target = self._role_mappings.get(name_or_role, name_or_role)

        # 2. Return explicit provider if already registered
        if target in self._providers:
            return self._providers[target]

        # 3. Handle 'ollama' or specific ollama model
        if target == "ollama" or target.startswith("ollama:"):
            model = target.split(":", 1)[1] if ":" in target else "qwen2.5-coder:7b-instruct"
            provider = OllamaProvider(model_name=model)
            self._providers[target] = provider
            return provider

        # 4. Handle 'openai'
        if target == "openai" or target.startswith("openai:"):
            model = target.split(":", 1)[1] if ":" in target else "gpt-4o"
            provider = OpenAICompatibleProvider(model_name=model)
            self._providers[target] = provider
            return provider

        # 5. Handle 'auto'
        if target == "auto":
            # Attempt to use local Ollama if reachable
            ollama = OllamaProvider()
            if ollama.is_available():
                self._providers["auto"] = ollama
                return ollama
            # Fall back to deterministic provider
            return self._providers["deterministic"]

        # Default fallback
        return self._providers["deterministic"]


# Global default registry instance
registry = ProviderRegistry()
