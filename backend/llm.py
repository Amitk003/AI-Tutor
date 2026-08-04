"""LLM API client.

The only module that talks to the outside AI provider. Everything else in the
app calls these functions. The provider must be OpenAI-compatible (OpenAI,
DeepSeek, Groq, OpenRouter, and similar all work).

Two jobs:
  embed(texts) - turn text into a list of numbers (for search).
  chat(system, user) - get a text answer from the chat model.
"""

import json
from typing import Any

import httpx

from backend import config


class LLMError(Exception):
    """Raised when the LLM API cannot be reached or returns an error."""


class LLMClient:
    """Small wrapper around the OpenAI-compatible HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or config.LLM_BASE_URL).rstrip("/")
        self.api_key = api_key or config.LLM_API_KEY
        self.timeout = timeout or config.LLM_TIMEOUT_SECONDS
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST to the API and return the JSON body, or raise LLMError."""
        if not self.api_key:
            raise LLMError("LLM_API_KEY is not set. See docs/setup.md.")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/{path}",
                    headers=self._headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM API unreachable: {exc}") from exc

        if resp.status_code >= 400:
            detail = resp.text[:300]
            raise LLMError(
                f"LLM API returned status {resp.status_code}: {detail}"
            )
        return resp.json()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts. Returns one vector per text."""
        if not texts:
            return []
        body = self._post(
            "embeddings",
            {"model": config.EMBED_MODEL, "input": texts},
        )
        # The API may return data out of order, so map by index.
        ordered = sorted(body["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in ordered]

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text."""
        return self.embed([text])[0]

    def chat(self, system: str, user: str) -> str:
        """Send one chat request and return the assistant text."""
        body = self._post(
            "chat/completions",
            {
                "model": config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
        )
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise LLMError(f"Unexpected LLM response shape: {json.dumps(body)[:300]}") from exc

    def ping(self) -> bool:
        """Check that the provider is reachable and the key works."""
        try:
            self.embed_one("ping")
            return True
        except LLMError:
            return False


# Shared client used across the app.
llm = LLMClient()
