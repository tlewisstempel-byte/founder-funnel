"""The only place that talks to a model provider (hard rule 6 in START_HERE.md).

To switch provider: add a class with the same `complete` method and register
it in `make_llm`. Nothing else in the code base changes.
"""

from __future__ import annotations

import json
import re
from typing import Callable


class LLM:
    model: str = ""

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        raise NotImplementedError

    def complete_json(self, system: str, user: str, max_tokens: int = 3000) -> dict:
        """Ask for JSON and parse it, tolerating code fences or stray prose."""
        text = self.complete(system + "\n\nReply with a single JSON object and nothing else.", user, max_tokens)
        return parse_json(text)


def parse_json(text: str) -> dict:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {text[:200]}")
    return json.loads(text[start : end + 1])


class AnthropicLLM(LLM):
    def __init__(self, api_key: str, model: str):
        import anthropic

        if not model:
            raise ValueError("Set LLM_MODEL (check the provider's current model names).")
        self._client = anthropic.Anthropic(api_key=api_key or None)
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")


class FakeLLM(LLM):
    """For tests and dry runs: returns whatever the responder function gives."""

    model = "fake"

    def __init__(self, responder: Callable[[str, str], str]):
        self._responder = responder
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        self.calls.append((system, user))
        return self._responder(system, user)


def make_llm(settings) -> LLM:
    if settings.llm_provider == "anthropic":
        return AnthropicLLM(settings.anthropic_api_key, settings.llm_model)
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
