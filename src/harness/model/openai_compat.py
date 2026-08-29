"""OpenAI-compatible request helpers. Local editors talk to this; Ollama is the backend."""

from __future__ import annotations

import json
from typing import Any

from finetune.everyday import DEFAULT_EVERYDAY_OLLAMA, is_tiny_model


def parse_chat_body(raw: bytes) -> dict[str, Any]:
    body = json.loads(raw or b"{}")
    if not isinstance(body, dict):
        raise ValueError("json object required")
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages required")
    model = str(body.get("model") or DEFAULT_EVERYDAY_OLLAMA)
    return {"model": model, "messages": messages, "stream": bool(body.get("stream"))}


def warn_tiny(model: str) -> str | None:
    if is_tiny_model(model):
        return (
            f"{model} is the 0.5B sidecar. Everyday laptop use should be "
            f"{DEFAULT_EVERYDAY_OLLAMA} (or qwen2.5-coder:7b / 14b)."
        )
    return None


def ollama_openai_url(host: str) -> str:
    return host.rstrip("/") + "/v1/chat/completions"


def models_payload(model: str) -> dict[str, Any]:
    return {
        "object": "list",
        "data": [{"id": model, "object": "model", "owned_by": "ollama"}],
    }
