"""OpenAI-compatible HTTP provider using standard library."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from howlcreate.providers.base import BaseProvider, ProviderResponse
from howl_provider_core import (
    Execution,
    Policy,
    ProviderError,
    guarded_opener,
    classify_failure,
    reported_metadata,
)


class OpenAICompatibleProvider(BaseProvider):
    """Provider for OpenAI, DeepSeek, vLLM, or any /v1/chat/completions endpoint."""

    sampling_capabilities = {"temperature": True, "seed": False, "top_p": False}

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
        policy: Policy | None = None,
    ):
        super().__init__(model_name=model_name)
        self.api_base = (
            api_base
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout
        self.policy = policy or Policy()
        self.policy.check_url(self.api_base)
        self.opener = guarded_opener(self.policy)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ProviderResponse:
        self.policy.check_url(self.api_base)
        start_time = time.time()
        url = f"{self.api_base}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req_body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_body, headers=headers, method="POST")

        execution = None
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                body = resp.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ProviderError("provider response exceeds 2 MB")
                data = json.loads(body.decode("utf-8"))

            meta = reported_metadata(body.decode("utf-8"), "openai-json")
            execution = Execution(
                "openai",
                "openai",
                "openai_compatible",
                "http",
                requested_model=self.model_name,
                model=meta["model"],
                usage=meta["usage"],
                request_id=meta["request_id"],
                inference_occurred=meta["inference_occurred"],
                elapsed_seconds=time.time() - start_time,
                raw_output_received=True,
                parse_status="FAILED",
            ).to_dict()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            usage = data.get("usage") or {}
            if not isinstance(content, str) or not content.strip():
                raise ProviderError("empty or non-text provider response")
            if not isinstance(usage, dict):
                raise ProviderError("invalid usage metadata")
            content = content.replace(self.api_key, "[REDACTED]") if self.api_key else content

            resp_obj = ProviderResponse(
                content=content,
                model=data.get("model") or "unknown",
                provider="openai_compatible",
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                latency_seconds=round(time.time() - start_time, 4),
            )
            execution.update(
                parse_status="VALID",
                deterministic=data.get("deterministic", False),
                mocked=data.get("mocked", False),
            )
            resp_obj.metadata["execution"] = execution
            parsed = resp_obj.extract_json()
            if parsed:
                resp_obj.structured_data = parsed
            return resp_obj

        except (
            urllib.error.URLError,
            OSError,
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
        ) as error:
            if isinstance(error, ProviderError):
                failure = error.failure
            elif isinstance(error, urllib.error.HTTPError):
                failure = classify_failure(str(error.code))
            else:
                failure = classify_failure("malformed" if execution else "provider unavailable")
            if execution is None:
                execution = Execution(
                    "openai",
                    "openai",
                    "openai_compatible",
                    "http",
                    requested_model=self.model_name,
                    elapsed_seconds=time.time() - start_time,
                ).to_dict()
            raise ProviderError(
                "HTTP provider failed; check configuration and response",
                failure=failure,
                execution=execution,
            ) from None
