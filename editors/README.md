# Drop-in editor settings

Three easy paths. Pick one. You do not need a GPU to copy these files.

| Path | What it does | Localhost works? |
| --- | --- | --- |
| VS Code tasks | Command Palette → Run Task → `python-vibe: ask` / `run` | Yes. Uses the jail in the integrated terminal. |
| Continue (VS Code) | Chat talks to `http://127.0.0.1:8081/v1` (Ollama proxy) | Yes. This changes the **brain**, not the jail. |
| Cursor MCP | `.cursor/mcp.json` starts `python -m harness mcp` as a child process | Yes. The editor calls the jail on this machine. No tunnel. |

One command from a python-vibe checkout (or `pip install -e .`):

```bash
python -m harness editors vscode   --project /path/to/your/app
python -m harness editors continue --project /path/to/your/app
python -m harness editors cursor   --project /path/to/your/app
```

Then:

1. `ollama pull llama3.1:8b`
2. For Continue chat: `PYTHONPATH=src python scripts/openai_compat.py` (or `python-vibe serve --project /path/to/your/app` and point the editor at `http://127.0.0.1:8090/v1`)
3. For tasks / MCP: no extra server

## Cursor Chat override (usually the hard path)

Cursor Settings → Models → Override OpenAI Base URL with `http://127.0.0.1:8081/v1` often **does not work**. Many builds send that request from a remote backend, which cannot see your loopback. A public HTTPS tunnel would reach the jail from the internet. Do not do that.

Use **MCP** (`editors cursor`) or **Run Task** (the VS Code `tasks.json` also works in Cursor). Those stay on this machine.

## What each file is

- `vscode/tasks.json` — `python-vibe ask` and `python-vibe run` with an input prompt
- `vscode/continue.yaml` — Continue `config.yaml` for the everyday 8B
- `cursor/mcp.json` — local stdio MCP (`ask` read-only, `run` needs `--allow-writes`). `python -m harness editors cursor` fills `__PYTHON__` with this machine’s interpreter and `__PROJECT__` with an absolute path.
