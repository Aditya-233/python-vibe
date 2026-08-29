"""Load and call a language model.

Supports a LoRA adapter through MLX and a local model through Ollama. This
is the only package whose output is not deterministic. It imports no other
package in the harness, so everything else can be tested without a model.
"""
