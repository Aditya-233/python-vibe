# Cursor: local MCP (easy) vs Chat override (usually hard)

## Easy — stays on this machine

```bash
python -m harness editors cursor --project /path/to/your/app
```

That writes `.cursor/mcp.json` with an absolute `--project`. Reload the window. Settings → MCP should show `python-vibe` with tools `ask` (read-only) and `run` (writes only if you add `--allow-writes` to the args).

The VS Code task file also works here (Cursor is a VS Code fork):

```bash
python -m harness editors vscode --project /path/to/your/app
```

Command Palette → Run Task → `python-vibe: ask` or `python-vibe: run`.

## Hard — Override OpenAI Base URL

`http://127.0.0.1:8081/v1` often fails because the request is sent from a remote backend, not from this laptop. A public tunnel would expose the jail. Do not do that.

Use MCP or Run Task instead.
