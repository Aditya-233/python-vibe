# Drop-in editor settings

One command. You do not need a GPU to copy these files.

| Path | What it does | Localhost works? |
| --- | --- | --- |
| Cursor | `.cursor/mcp.json` + `.vscode/tasks.json` | Yes. Cursor starts the jail as a child process. No tunnel. |
| VS Code tasks | Command Palette → Run Task → `python-vibe: ask` / `run` | Yes. Uses the jail in the integrated terminal. |
| Continue (VS Code) | Chat talks to `http://127.0.0.1:8081/v1` (Ollama proxy) | Yes. This changes the **brain**, not the jail. |
| Zed | Merges `context_servers` into `.zed/settings.json` | Yes. Same stdio jail. Existing Zed keys stay. |

```bash
python-vibe editors cursor                 # this folder (default)
python-vibe editors cursor --allow-writes  # let chat edit files
python-vibe editors cursor --global        # every workspace, merge only
python-vibe editors vscode
python-vibe editors continue
python-vibe editors zed
```

`--project` defaults to `.`. Then:

1. `ollama pull llama3.1:8b`
2. Reload the window. Customize → MCP → enable `python-vibe`
3. Cursor Chat override of `127.0.0.1` is the hard path. Do not use a tunnel.

## What each file is

- `vscode/tasks.json` — `python-vibe ask` and `python-vibe run` with an input prompt
- `vscode/continue.yaml` — Continue `config.yaml` for the everyday 8B
- `cursor/mcp.json` — portable template (`${workspaceFolder}`, no machine path)
