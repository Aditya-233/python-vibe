"""Serve the agent over HTTP on the local machine only.

An HTTP request that reaches the agent can change files on the machine the
server runs on. Because of that, file changes are disabled unless the
person starting the server passes `--allow-writes`. The path restriction,
the draft guard and the `.bak` backup all still apply; this flag is an
additional outer control, not a replacement for them.

    python -m harness serve --project ~/app
    curl -s localhost:8090/health
    curl -s localhost:8090/v1/layout -d '{}'
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from harness.agent import Agent, AgentOptions
from harness.scan.layout import render_layout
from harness.scan.project_brief import classify_project, render_brief

HOST = "127.0.0.1"
MAX_BODY = 64 * 1024
READ_ONLY_ROUTES = ("/v1/brief", "/v1/layout", "/v1/ask")
WRITE_ROUTES = ("/v1/run",)


def make_handler(project: Path, *, allow_writes: bool, model: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "python-vibe"
        protocol_version = "HTTP/1.1"

        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            # Say the connection is finished. A client left waiting for more
            # blocks until its own timeout, which is what happened on Windows.
            self.send_header("connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def _body(self) -> dict | None:
            length = int(self.headers.get("content-length") or 0)
            if length > MAX_BODY:
                self._send(413, {"error": "body too large"})
                return None
            raw = self.rfile.read(length) if length else b"{}"
            try:
                parsed = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"error": "invalid json"})
                return None
            if not isinstance(parsed, dict):
                self._send(400, {"error": "object required"})
                return None
            return parsed

        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/health":
                self._send(404, {"error": "no such route"})
                return
            self._send(
                200,
                {
                    "ok": True,
                    "project": str(project),
                    "allow_writes": allow_writes,
                    "model": model,
                    "routes": list(READ_ONLY_ROUTES)
                    + (list(WRITE_ROUTES) if allow_writes else []),
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            if self.path not in READ_ONLY_ROUTES + WRITE_ROUTES:
                self._send(404, {"error": "no such route"})
                return
            if self.path in WRITE_ROUTES and not allow_writes:
                self._send(
                    403,
                    {
                        "error": "this server is read-only",
                        "fix": "restart it with --allow-writes",
                    },
                )
                return
            payload = self._body()
            if payload is None:
                return
            scope = str(payload.get("scope") or "")
            if self.path == "/v1/brief":
                brief = classify_project(project, scope)
                self._send(200, {"brief": render_brief(brief, scope=scope)})
                return
            if self.path == "/v1/layout":
                self._send(200, {"layout": render_layout(project)})
                return
            task = str(payload.get("task") or "").strip()
            if not task:
                self._send(400, {"error": "task required"})
                return
            options = AgentOptions(
                project=project,
                task=task,
                model=str(payload.get("model") or model),
                scope=scope,
                steps=int(payload.get("steps") or 20),
                allow_writes=allow_writes and self.path in WRITE_ROUTES,
            )
            try:
                result = Agent(options).run()
            except (ValueError, OSError) as exc:
                self._send(400, {"error": str(exc)})
                return
            self._send(200, result.as_dict())

        def log_message(self, fmt: str, *args) -> None:
            print(f"{self.address_string()} - {fmt % args}")

    return Handler


def serve(
    project: Path, *, port: int = 8090, allow_writes: bool = False, model: str = ""
) -> int:
    handler = make_handler(project, allow_writes=allow_writes, model=model)
    httpd = ThreadingHTTPServer((HOST, port), handler)
    mode = "read-write" if allow_writes else "read-only"
    print(f"python-vibe on http://{HOST}:{port}  project {project}  {mode}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0
