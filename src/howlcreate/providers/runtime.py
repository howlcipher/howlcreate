"""Call accounting and per-response identity for all pipeline provider seams."""

import time

from howl_provider_core import CallBudget, CommandConfig, CommandProvider, Execution

from howlcreate.providers.base import BaseProvider, ProviderResponse


class RemoteCommandProvider(BaseProvider):
    def __init__(self, config: CommandConfig):
        super().__init__(config.model or "unknown")
        self.adapter = CommandProvider(config)
        self.requested_provider = "command"

    def generate(self, prompt, system_prompt="", temperature=0.7, json_mode=False):
        text, execution = self.adapter.generate(system_prompt + "\n" + prompt)
        return ProviderResponse(
            text,
            execution.model or "unknown",
            "command",
            metadata={"execution": execution.to_dict()},
        )


class TrackedProvider(BaseProvider):
    def __init__(self, provider: BaseProvider, budget: CallBudget, requested: str):
        super().__init__(provider.model_name)
        self.provider = provider
        self.budget = budget
        self.requested = requested
        self.executions: list[dict] = []

    def generate(self, prompt, **kwargs):
        return self.generate_for("unspecified", prompt, **kwargs)

    def generate_for(self, operation, prompt, **kwargs):
        if isinstance(self.provider, FallbackProvider):
            response, executions = self.provider.generate_budgeted(
                operation, prompt, self.budget, **kwargs
            )
            self.executions.extend(executions)
            return response
        self.budget.consume(type(self.provider).__name__)
        started = time.monotonic()
        try:
            response = self.provider.generate_for(operation, prompt, **kwargs)
        except BaseException:
            self.budget.events[-1]["status"] = "FAILED"
            raise
        self.budget.events[-1]["status"] = "COMPLETE"
        execution = (
            response.metadata.get("execution")
            or Execution(
                self.requested,
                type(self.provider).__name__,
                response.provider,
                type(self.provider).__name__,
                model=response.model,
                deterministic=response.provider == "deterministic",
                mocked=response.provider == "deterministic",
                inference_occurred=False if response.provider == "deterministic" else None,
                elapsed_seconds=time.monotonic() - started,
            ).to_dict()
        )
        execution["requested_provider"] = self.requested
        execution["operation"] = operation
        if self.requested == "auto" and response.provider == "deterministic":
            execution["fallback_reason"] = "No authorized remote provider configured"
        response.metadata["execution"] = execution
        self.executions.append(execution)
        return response


class FallbackProvider(BaseProvider):
    """An explicit operator-constructed chain. Attempts share the enclosing call budget."""

    def __init__(self, providers: list[BaseProvider], requested: str):
        if not providers:
            raise ValueError("fallback requires at least one provider")
        super().__init__(providers[0].model_name)
        self.providers = providers
        self.requested_provider = requested

    def generate(self, prompt, **kwargs):
        raise ValueError("fallback must execute through a budgeted provider seam")

    def generate_budgeted(self, operation, prompt, budget, **kwargs):
        from howl_provider_core import BudgetExceeded, ProviderError

        executions = []
        for index, provider in enumerate(self.providers):
            tracked = TrackedProvider(provider, budget, self.requested_provider)
            try:
                response = tracked.generate_for(operation, prompt, **kwargs)
            except BudgetExceeded:
                raise
            except (ProviderError, RuntimeError):
                continue
            executions.extend(tracked.executions)
            execution = response.metadata["execution"]
            if index:
                execution["fallback_reason"] = "Earlier authorized provider attempts failed"
                execution["fallback_attempt"] = index
            return response, executions
        raise ProviderError("authorized fallback providers exhausted")
