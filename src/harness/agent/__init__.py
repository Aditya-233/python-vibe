"""The agent loop and its public types.

`Agent` runs one task. `AgentOptions` describes how to run it and
`AgentResult` describes what happened. Every layer below this one works
without a model, which is what allows the harness to be tested offline.
"""

from harness.agent.loop import Agent, Question
from harness.agent.options import AgentOptions, AgentResult, Step

__all__ = ["Agent", "AgentOptions", "AgentResult", "Question", "Step"]
