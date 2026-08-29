---
title: Using python-vibe
description: Run the agent as a Python library, as one command, or over HTTP on 127.0.0.1. Settings, read-only runs, and the server routes.
date: 2026-08-29
---

Three ways to run the same agent: as a Python library, as one command, or
over HTTP on your own machine.

## Library

```python
from pathlib import Path
from harness import Agent, AgentOptions

agent = Agent(AgentOptions(project=Path("~/app"), scope="src"))
result = agent.run("add multiply(a, b) and a unit test")

result.ok        # True when the agent finished the task
result.summary   # its closing sentence
result.writes    # files it changed
result.steps     # every turn, in order
result.refusals  # what the harness stopped, and why
```

### Settings

| Field | Default | What it does |
| --- | --- | --- |
| `project` | required | Directory the agent may read and write inside |
| `task` | `""` | What you are asking for |
| `model` | `llama3.1:8b` | Ollama model name |
| `engine` | `ollama` | `ollama` or `mlx` |
| `scope` | `""` | Stay inside this subdirectory |
| `skills` | `()` | Skill names to load. Empty means choose from the task. Catalog: [Skills]({{ '/skills/' | relative_url }}) |
| `steps` | `20` | Maximum model turns before the run stops |
| `max_tokens` | `700` | Maximum length of one model reply |
| `allow_writes` | `True` | When `False`, patch, edit and run are refused |
| `record` | `None` | File to append redacted turns to |
| `on_event` | `None` | Called with progress messages |
| `on_question` | `None` | Called when the agent needs you to choose |

### Read-only runs

```python
options = AgentOptions(project=Path("~/app"), allow_writes=False)
Agent(options).run("what would you change in src/app.py?")
```

Nothing is written. `patch`, `edit` and `run` are refused before any tool
sees them, and the prompt says the run is read-only.

### When the agent needs to know something

A task such as `"clean this up"` names no file and no function. Rather than
guessing, the harness asks before it calls the model:

```python
def choose(question):
    print(question.render())
    return input("> ")

Agent(AgentOptions(project=..., on_question=choose)).run("clean this up")
```

Without `on_question` the run stops immediately and returns the question:

```python
result.stopped   # "question"
result.summary   # the question and the options
result.writes    # ()
```

## Install

The harness uses only the standard library, so there is nothing to build and
the same three commands work on macOS, Linux and Windows.

```bash
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
pip install -e .
```

That gives you a `python-vibe` command. No `PYTHONPATH`, no version-pinned
interpreter, no script paths:

| | Before | After |
| --- | --- | --- |
| macOS / Linux | `PYTHONPATH=src python3.13 scripts/agent.py --project ~/app "..."` | `python-vibe run ~/app "..."` |
| Windows | did not work: `PYTHONPATH=src` is not valid in cmd or PowerShell | `python-vibe run C:\app "..."` |

Training on Apple Silicon needs extras: `pip install -e ".[train]"`.
Publishing to the Hub needs `pip install -e ".[hub]"`.

Paths are always written with forward slashes, on every platform, because
the model is shown them and copies them back.

### What `run` may do to your project

`run` changes files inside the folder you give it, keeps a `.bak` copy of
anything it edits, and **runs that project's test suite** to check its own
work. If you would rather it did nothing, use `ask`, or pass
`allow_writes=False` and `--dry-run`, which refuse every change and never
run anything.

Some fixes need no model at all. A misspelled name that Python cannot
resolve, or a rename you asked for by name, are corrected directly; the
suite is then run once, and if it passes the task ends there.

## Command line

```bash
python -m harness brief  ~/app                              # no model
python -m harness route  "what does compute_total return?"  # no model
python -m harness layout ~/app                              # no model
python -m harness ask    ~/app "what does compute_total return?"
python -m harness run    ~/app "add multiply(a, b) and a test"
python -m harness run    ~/app "..." --dry-run --scope src
python -m harness serve    --project ~/app
python -m harness mcp      --project ~/app          # stdio, for an editor
python -m harness editors  vscode --project ~/app   # drop-in tasks.json
python -m harness editors  zed     --project ~/app   # merge .zed/settings.json
```

`brief`, `layout`, and `route` never call a model. `ask` is always read-only. `run`
writes unless you pass `--dry-run`. Add `--json` for machine-readable
output, `-v` for tool results.

## HTTP server

```bash
python -m harness serve --project ~/app --port 8090
```

Binds `127.0.0.1` only. **File changes are off by default**, because an
HTTP request that reaches the agent can change files on the machine the
server runs on.

| Route | Method | Needs `--allow-writes` |
| --- | --- | --- |
| `/health` | GET | no |
| `/v1/brief` | POST | no |
| `/v1/layout` | POST | no |
| `/v1/ask` | POST | no |
| `/v1/models` | GET | no |
| `/v1/chat/completions` | POST | writes only with `--allow-writes` |
| `/v1/run` | POST | yes |

```bash
curl -s localhost:8090/health
curl -s localhost:8090/v1/layout -d '{}'
curl -s localhost:8090/v1/ask -d '{"task":"what does compute_total return?"}'
curl -s localhost:8090/v1/models
```

`POST /v1/chat/completions` takes the last user message as the task and
returns an OpenAI-shaped reply. `stream` is refused. A write task on a
read-only server is `403`. Point VS Code and other OpenAI-compatible
editors at `http://127.0.0.1:8090/v1`, or copy drop-in files with
`python-vibe editors vscode --project ~/app`. Details:
[local editor]({{ '/local-editor/' | relative_url }}).


Without `--allow-writes`, `/v1/run` answers `403` and says how to enable it.
The path restriction, the draft guard and the `.bak` backup apply in every
mode; the flag is an additional control, not a replacement for them.
