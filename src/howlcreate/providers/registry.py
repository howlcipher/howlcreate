"""Explicit provider registry. Auto never discovers or selects local inference."""

from typing import Dict

from howl_provider_core import Policy, ProviderError
from howlcreate.providers.base import BaseProvider
from howlcreate.providers.deterministic import DeterministicProvider
from howlcreate.providers.ollama import OllamaProvider
from howlcreate.providers.openai_compatible import OpenAICompatibleProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {"deterministic": DeterministicProvider()}
        self._role_mappings: Dict[str, str] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def assign_role(self, role: str, provider_name: str) -> None:
        self._role_mappings[role] = provider_name

    def get_provider(
        self, name_or_role: str = "auto", *, allow_local: bool = False
    ) -> BaseProvider:
        target = self._role_mappings.get(name_or_role, name_or_role)
        policy = Policy(allow_local=allow_local)
        if target == "auto":
            # No implicit egress, availability probes or service launch.
            target = "deterministic"
        if target in self._providers:
            provider = self._providers[target]
            if isinstance(provider, OllamaProvider):
                policy.check_provider("ollama")
                provider.allow_local = allow_local
            provider.requested_provider = name_or_role
            return provider
        if target == "ollama" or target.startswith("ollama:"):
            policy.check_provider("ollama")
            model = target.partition(":")[2] or "qwen2.5-coder:7b-instruct"
            provider = OllamaProvider(model_name=model)
            provider.allow_local = allow_local
        elif target == "openai" or target.startswith("openai:"):
            provider = OpenAICompatibleProvider(
                model_name=target.partition(":")[2] or "gpt-4o", policy=policy
            )
        else:
            raise ProviderError("unknown explicit provider; configure a registered provider")
        provider.requested_provider = name_or_role
        return provider


registry = ProviderRegistry()
