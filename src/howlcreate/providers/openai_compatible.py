"""OpenAI-compatible HTTP provider using standard library."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from howlcreate.providers.base import BaseProvider, ProviderResponse


class OpenAICompatibleProvider(BaseProvider):
    """Provider for OpenAI, DeepSeek, vLLM, or any /v1/chat/completions endpoint."""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
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

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ProviderResponse:
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

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            usage = data.get("usage", {})

            resp_obj = ProviderResponse(
                content=content,
                model=self.model_name,
                provider="openai_compatible",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                latency_seconds=round(time.time() - start_time, 4),
            )
            parsed = resp_obj.extract_json()
            if parsed:
                resp_obj.structured_data = parsed
            return resp_obj

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI compatible API error ({e.code}): {err_msg}") from e
        except Exception as e:
            raise RuntimeError(f"OpenAI compatible provider failed: {e}") from e
