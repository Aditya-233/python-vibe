"""Layer: talking to weights. The only layer that is not deterministic.

MLX LoRA or Ollama, loaded once and reused. Imports no other harness layer
so the rest of the harness stays testable without a model.
"""
