# Security Policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Email **info@molecare.co.uk** with:

- what the issue is and where in the code it lives
- how to reproduce it
- what an attacker could do with it

You should get an acknowledgement within **3 working days**.

The Security tab "Report a vulnerability" button is also fine if enabled.

## Scope

In scope:

- the HTTP sidecar (`scripts/serve.py`) — unbounded body size, binding
  `0.0.0.0` by default, SSRF if `OLLAMA_HOST` is attacker-controlled
- harness misses that ship a **blocked** class of output (`pass` on a leaked
  key or `curl|sh`)
- secrets committed to the repository
- dependency issues reachable from `scripts/serve.py` or the harness

Out of scope (open a normal issue instead):

- paraphrase evasion of string rules
- model quality / ugly Python
- needing a Hugging Face token to train

## Data safety

- Never commit `.env`, `HF_TOKEN`, or adapter folders
- Never paste a real API key into an issue, even as a "repro"
