---
name: call-http
description: Adds one urllib.request helper that GETs or POSTs JSON. Use for HTTP API, REST, curl-shaped fetches. Never emit curl or a pipe to sh.
---

stdlib urllib only. Timeout. Raise on HTTP errors. No curl. No secrets.

Action: edit
Path: pkg/fetch_json.py
import json
import urllib.error
import urllib.request
from typing import Any


def fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code} for {url}") from exc
    if not isinstance(payload, dict):
        raise ValueError("json object required")
    return payload
