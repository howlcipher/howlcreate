"""Ollama local model provider using standard library HTTP."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from howlcreate.providers.base import BaseProvider, ProviderResponse
from howl_provider_core import Policy, ProviderError, guarded_opener


class OllamaProvider(BaseProvider):
    """Local inference provider communicating with Ollama over HTTP."""

    def __init__(
        self,
        model_name: str = "qwen2.5-coder:7b-instruct",
        host: Optional[str] = None,
        timeout: int = 90,
    ):
        super().__init__(model_name=model_name)
        self.host = host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        policy = Policy(allow_local=getattr(self, "allow_local", False))
        policy.check_provider("ollama")
        policy.check_url(self.host)
        """Check if the Ollama endpoint is reachable."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with guarded_opener(policy).open(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> ProviderResponse:
        policy = Policy(allow_local=getattr(self, "allow_local", False))
        policy.check_provider("ollama")
        policy.check_url(self.host)
        start_time = time.time()
        url = f"{self.host}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if json_mode:
            payload["format"] = "json"

        req_body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with guarded_opener(policy).open(req, timeout=self.timeout) as resp:
                body = resp.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ProviderError("provider response exceeds 2 MB")
                data = json.loads(body.decode("utf-8"))

            content = data.get("message", {}).get("content", "")
            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)

            resp_obj = ProviderResponse(
                content=content,
                model=self.model_name,
                provider="ollama",
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count,
                latency_seconds=round(time.time() - start_time, 4),
            )
            # Pre-parse json if possible
            parsed = resp_obj.extract_json()
            if parsed:
                resp_obj.structured_data = parsed
            return resp_obj

        except Exception as error:
            raise ProviderError("Ollama provider failed; check explicit configuration") from error
