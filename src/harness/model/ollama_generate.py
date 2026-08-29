"""Call a local/cloud Ollama model. Weights stay in Ollama; this process is tiny."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Sequence


class OllamaGenerate:
    def __init__(
        self,
        model: str,
        system: str,
        host: str | None = None,
        timeout: float = 180,
    ) -> None:
        self.model = model
        self.system = system
        self.timeout = timeout
        self.host = (host or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip(
            "/"
        )

    def __call__(
        self, prompt: str, history: Sequence[dict[str, str]] | None = None
    ) -> str:
        messages: list[dict[str, str]] = [{"role": "system", "content": self.system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        body = json.dumps(
            {
                "model": self.model,
                "stream": False,
                "messages": messages,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ollama {self.host} unreachable: {exc}") from exc
        message = payload.get("message") or {}
        return str(message.get("content") or "")

    def healthy(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=2) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False
