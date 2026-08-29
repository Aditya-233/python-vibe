"""Layer: what ships and what is refused. Deterministic, no model.

The draft guard (`PythonVibeGuard`), the generate/revise/fallback loop, and
the loop-level refusals. This layer is the safety boundary: it must never
import a layer that can write.
"""
