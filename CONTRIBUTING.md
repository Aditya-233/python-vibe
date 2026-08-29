# Contributing to python-vibe

Thanks for being here. This repo is small: one 0.5B LoRA, a deterministic
harness, and stdlib HTTP. It is a good first open-source project if you keep
the rules below.

## Rules that are not negotiable

- The harness stays **deterministic**. Do not add a keyword router on the user
  prompt that skips `PythonVibeGuard`.
- Do not commit `.safetensors`, `.env`, tokens, or real hostnames.
- Do not teach the model to comment on moles or lesions (PV004 already blocks
  that — this is a coding model, not [MoleCare/skincare-qa](https://github.com/MoleCare/skincare-qa)).
- Do not add `curl … | sh` examples the harness would block (PV003).

## Getting set up

```bash
git clone https://github.com/YauhenBichel/python-vibe.git
cd python-vibe
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -q
```

You do **not** need a Hugging Face token, Ollama, or a GPU to run the harness
tests. Training the tiny LoRA uses MLX on Apple Silicon (Homebrew Python 3.13).
Everyday agent work uses Ollama 8B+ — see [AGENTS.md](./AGENTS.md) and
[docs/local-editor.md](./docs/local-editor.md).

Uploads go to **your** Hub namespace (`HF_USER=yourname` or `HF_REPO=…`), never
to the official weights repo unless you are a maintainer. Anyone can download
the public adapters without an account.

## What you may add

- More **short** Python training pairs (stdlib first, type hints, no secrets)
- A harness rule with **two fixtures**: one string that must `block`, one
  near-miss that must `pass`
- Docs, CI, and eval prompts

## Before you open a pull request

- [ ] `PYTHONPATH=src python -m unittest discover -s tests -q` passes
- [ ] New pairs do not include live keys or `curl|sh`
- [ ] No secrets, real hostnames, or personal data
- [ ] One concern per PR

## Pick an issue by level

Start at [Welcome — how to pick an issue](https://github.com/YauhenBichel/python-vibe/discussions/10).
Design questions go in [Discussions](https://github.com/YauhenBichel/python-vibe/discussions), not a drive-by PR.

| Level | Label | Seeded issues |
| --- | --- | --- |
| Very junior | [`good first issue`](https://github.com/YauhenBichel/python-vibe/labels/good%20first%20issue) | [#1](https://github.com/YauhenBichel/python-vibe/issues/1) PV005 test · [#2](https://github.com/YauhenBichel/python-vibe/issues/2) `.env.example` · [#3](https://github.com/YauhenBichel/python-vibe/issues/3) one training pair · [#4](https://github.com/YauhenBichel/python-vibe/issues/4) README clone path |
| Intermediate | [`intermediate`](https://github.com/YauhenBichel/python-vibe/labels/intermediate) | [#5](https://github.com/YauhenBichel/python-vibe/issues/5) localhost + body cap · [#6](https://github.com/YauhenBichel/python-vibe/issues/6) HTTP sidecar tests · [#7](https://github.com/YauhenBichel/python-vibe/issues/7) best val checkpoint |
| Research | [`research`](https://github.com/YauhenBichel/python-vibe/labels/research) | [#8](https://github.com/YauhenBichel/python-vibe/issues/8) guard evasion · [#9](https://github.com/YauhenBichel/python-vibe/issues/9) 45 pairs vs style prior |

Open threads: [fused weights](https://github.com/YauhenBichel/python-vibe/discussions/11) · [stdlib vs FastAPI](https://github.com/YauhenBichel/python-vibe/discussions/12) · [eval protocol](https://github.com/YauhenBichel/python-vibe/discussions/13) · [train without MLX](https://github.com/YauhenBichel/python-vibe/discussions/14).

## Reporting security issues

Do **not** open a public issue. See [SECURITY.md](./SECURITY.md).

## Licence

By contributing you agree that your contributions are licensed under the
[Apache-2.0 licence](./LICENSE) that covers this project.
