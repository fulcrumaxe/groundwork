"""LLM provider abstraction: OpenAI-compatible API with offline fallback.

Default endpoint is Ollama (http://localhost:11434/v1). Any OpenAI-compatible
server works via env: GW_BASE_URL, GW_API_KEY, GW_MODEL. When no server is
reachable, TemplateProvider generates deterministic exercises offline so the
MVP works with no cloud account (PRD goal).
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    via: str  # 'llm' | 'template'


class Provider:
    def complete(self, prompt: str) -> LLMResult:
        raise NotImplementedError


class OpenAICompatProvider(Provider):
    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, timeout: int = 60):
        self.base_url = (base_url or os.environ.get("GW_BASE_URL",
                                                     "http://localhost:11434/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("GW_API_KEY", "ollama")
        self.model = model or os.environ.get("GW_MODEL", "qwen2.5-coder:7b")
        self.timeout = timeout

    def complete(self, prompt: str) -> LLMResult:
        body = json.dumps({
            "model": self.model, "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            self.base_url + "/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.load(r)
        return LLMResult(data["choices"][0]["message"]["content"], "llm")


class TemplateProvider(Provider):
    """Deterministic offline generator: schema-valid exercises, no model."""

    def complete(self, prompt: str) -> LLMResult:
        return LLMResult("", "template")


def get_provider() -> Provider:
    """LLM when GW_NO_LLM is unset and a server answers; else offline."""
    if os.environ.get("GW_NO_LLM"):
        return TemplateProvider()
    p = OpenAICompatProvider(timeout=5)
    try:
        p.complete("ping")
        return OpenAICompatProvider()
    except Exception:
        return TemplateProvider()


EXERCISE_SCHEMA_HINT = (
    "Return strict JSON only: a list of objects with keys "
    "type (int), front (str), back (str), payload (object).")


def draft_exercises(provider: Provider, concept: dict, snippet: str,
                    types: list[int]) -> list[dict] | None:
    """Ask the LLM for exercise drafts; None when offline/template."""
    if isinstance(provider, TemplateProvider):
        return None
    prompt = (f"Create one code-comprehension exercise of each of these types "
              f"{types} about `{concept['name']}` ({concept['kind']}) "
              f"defined in {concept['file']}:{concept['line']}.\n"
              f"Source:\n{snippet[:2000]}\n{EXERCISE_SCHEMA_HINT}")
    try:
        res = provider.complete(prompt)
        start, end = res.text.find("["), res.text.rfind("]")
        if start < 0 or end < 0:
            return None
        items = json.loads(res.text[start:end + 1])
        return items if isinstance(items, list) else None
    except Exception:
        return None
