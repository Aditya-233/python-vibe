# Contributing

Public repo: [YauhenBichel/python-vibe](https://github.com/YauhenBichel/python-vibe).

1. Open an issue before a large change.
2. Work on a named branch (`feat/…`, `fix/…`). Do not commit to `main`.
3. Keep the harness deterministic. Do not add keyword routers around the model.
4. Weights stay on Hugging Face (`YauhenBichel/python-vibe-0.5b`). Do not commit `.safetensors`.
5. Run `PYTHONPATH=src python -m unittest discover -s tests -q` before you push.

License is Apache-2.0 (see `LICENSE`).
