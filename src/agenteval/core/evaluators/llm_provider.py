"""LLM provider adapter for sending scoring prompts to LLM APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMResponse:
    """Parsed response from an LLM provider."""

    text: str
    model: str
    usage: dict[str, int]


class LLMProviderError(Exception):
    """Raised when an LLM provider call fails."""


class LLMProvider:
    """Abstract interface for LLM API providers.

    Subclass and override ``_endpoint``, ``_build_request_body``,
    and ``_parse_response`` for each supported provider.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or ""
        self._model = model or ""

    @property
    def model_id(self) -> str:
        return self._model

    def complete(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        """Send a prompt and return the parsed response."""
        url = self._endpoint()
        body = self._build_request_body(prompt, max_tokens=max_tokens)
        headers = self._headers()

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
                resp_data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            msg = f"LLM API HTTP error {exc.code}"
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                msg = f"{msg}: {detail}"
            except Exception:  # noqa: BLE001
                pass
            raise LLMProviderError(msg) from exc
        except urllib.error.URLError as exc:
            raise LLMProviderError(f"LLM API network error: {exc.reason}") from exc
        except Exception as exc:
            raise LLMProviderError(f"LLM API error: {exc}") from exc

        return self._parse_response(resp_data)

    def _endpoint(self) -> str:
        raise NotImplementedError

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
        }

    def _build_request_body(self, prompt: str, *, max_tokens: int = 1024) -> dict[str, Any]:
        raise NotImplementedError

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    """Provider for the Anthropic Messages API."""

    ENV_KEY = "ANTHROPIC_API_KEY"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        key = api_key or os.environ.get(self.ENV_KEY, "")
        mdl = model or "claude-sonnet-4-5-20250929"
        super().__init__(api_key=key, model=mdl)

    def _endpoint(self) -> str:
        return "https://api.anthropic.com/v1/messages"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
        }

    def _build_request_body(self, prompt: str, *, max_tokens: int = 1024) -> dict[str, Any]:
        return {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        content_blocks = data.get("content", [])
        text = ""
        for block in content_blocks:
            if block.get("type") == "text":
                text += block.get("text", "")

        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            model=data.get("model", self._model),
            usage={
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )


class OpenAIProvider(LLMProvider):
    """Provider for the OpenAI Chat Completions API."""

    ENV_KEY = "OPENAI_API_KEY"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        key = api_key or os.environ.get(self.ENV_KEY, "")
        mdl = model or "gpt-4o"
        super().__init__(api_key=key, model=mdl)

    def _endpoint(self) -> str:
        return "https://api.openai.com/v1/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    def _build_request_body(self, prompt: str, *, max_tokens: int = 1024) -> dict[str, Any]:
        return {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        choices = data.get("choices", [])
        text = ""
        if choices:
            text = choices[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            model=data.get("model", self._model),
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
        )
