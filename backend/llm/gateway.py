"""
LLM Gateway Abstraction Layer.
Defines common interface and factory provider contracts for open-source LLMs (Ollama, vLLM).
Provides generate(), stream(), health(), and count_tokens() across all providers.
"""

from abc import ABC, abstractmethod
import json
from typing import Any, AsyncGenerator, Callable, Dict, Optional
import httpx
from loguru import logger

from backend.core.config import settings
from backend.core.exceptions import LLMServiceException
from backend.llm.token_budget import count_tokens as approx_count_tokens


class BaseLLMGateway(ABC):
    """Abstract interface shared across all LLM inference providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of provider (e.g. 'ollama', 'vllm')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of model (e.g. 'qwen2.5:3b-instruct')."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates complete LLM text response."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Streams LLM text tokens asynchronously."""
        pass

    @abstractmethod
    async def health(self) -> bool:
        """Returns True if inference service provider is online and healthy."""
        pass

    def count_tokens(self, text: str) -> int:
        """Counts or approximates token length of text."""
        return approx_count_tokens(text)


class OllamaGateway(BaseLLMGateway):
    """Ollama local LLM inference provider implementation."""

    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
        client_factory: Callable[..., httpx.AsyncClient] = httpx.AsyncClient,
    ):
        self._model = model or settings.OLLAMA_MODEL_NAME
        self._host = host or settings.OLLAMA_BASE_URL
        self._client_factory = client_factory

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    async def health(self) -> bool:
        """Pings Ollama service health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self._host}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        logger.info("OllamaGateway generate request: model={m} host={h}", m=self._model, h=self._host)
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": (parameters or {}).get("temperature", settings.LLM_TEMPERATURE),
                "top_p": (parameters or {}).get("top_p", settings.LLM_TOP_P),
                "num_predict": (parameters or {}).get("max_tokens", settings.MAX_OUTPUT_TOKENS),
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            async with self._client_factory(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self._host}/api/generate", json=payload)
                res.raise_for_status()
                answer = res.json().get("response", "").strip()
                if answer:
                    return answer
                raise LLMServiceException("Ollama returned an empty response.")
        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise
            logger.warning("Ollama request failed: {err}", err=str(e))
            raise LLMServiceException("The Ollama inference service is unavailable.", {"provider": "ollama"}) from e

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        logger.info("OllamaGateway stream request: model={m}", m=self._model)
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": (parameters or {}).get("temperature", settings.LLM_TEMPERATURE),
                "top_p": (parameters or {}).get("top_p", settings.LLM_TOP_P),
                "num_predict": (parameters or {}).get("max_tokens", settings.MAX_OUTPUT_TOKENS),
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            async with self._client_factory(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", f"{self._host}/api/generate", json=payload) as res:
                    res.raise_for_status()
                    async for line in res.aiter_lines():
                        if not line:
                            continue
                        event = json.loads(line)
                        if event.get("error"):
                            raise LLMServiceException(str(event["error"]), {"provider": "ollama"})
                        token = event.get("response", "")
                        if token:
                            yield token
        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise
            logger.warning("Ollama streaming request failed: {err}", err=str(e))
            raise LLMServiceException("The Ollama inference service is unavailable.", {"provider": "ollama"}) from e


class VLLMGateway(BaseLLMGateway):
    """vLLM high-throughput OpenAI-compatible inference provider implementation."""

    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
        client_factory: Callable[..., httpx.AsyncClient] = httpx.AsyncClient,
    ):
        self._model = model or settings.OLLAMA_MODEL_NAME
        self._host = host or settings.VLLM_BASE_URL
        self._client_factory = client_factory

    @property
    def provider_name(self) -> str:
        return "vllm"

    @property
    def model_name(self) -> str:
        return self._model

    async def health(self) -> bool:
        """Pings vLLM health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self._host}/health")
                return res.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        logger.info("VLLMGateway generate request: model={m}", m=self._model)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": (parameters or {}).get("temperature", settings.LLM_TEMPERATURE),
            "top_p": (parameters or {}).get("top_p", settings.LLM_TOP_P),
            "max_tokens": (parameters or {}).get("max_tokens", settings.MAX_OUTPUT_TOKENS),
            "stream": False,
        }
        try:
            async with self._client_factory(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
                res = await client.post(f"{self._host.rstrip('/')}/chat/completions", json=payload)
                res.raise_for_status()
                answer = res.json()["choices"][0]["message"]["content"].strip()
                if answer:
                    return answer
                raise LLMServiceException("vLLM returned an empty response.")
        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise
            logger.warning("vLLM request failed: {err}", err=str(e))
            raise LLMServiceException("The vLLM inference service is unavailable.", {"provider": "vllm"}) from e

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        logger.info("VLLMGateway stream request: model={m}", m=self._model)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": (parameters or {}).get("temperature", settings.LLM_TEMPERATURE),
            "top_p": (parameters or {}).get("top_p", settings.LLM_TOP_P),
            "max_tokens": (parameters or {}).get("max_tokens", settings.MAX_OUTPUT_TOKENS),
            "stream": True,
        }
        try:
            async with self._client_factory(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", f"{self._host.rstrip('/')}/chat/completions", json=payload) as res:
                    res.raise_for_status()
                    async for line in res.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line.removeprefix("data:").strip()
                        if data == "[DONE]":
                            return
                        event = json.loads(data)
                        token = event.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if token:
                            yield token
        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise
            logger.warning("vLLM streaming request failed: {err}", err=str(e))
            raise LLMServiceException("The vLLM inference service is unavailable.", {"provider": "vllm"}) from e


class LLMGatewayFactory:
    """Factory resolving configured BaseLLMGateway provider instance."""

    @staticmethod
    def get_gateway(provider: Optional[str] = None) -> BaseLLMGateway:
        prov = provider or settings.DEFAULT_LLM_PROVIDER
        if prov.lower() == "vllm":
            return VLLMGateway()
        return OllamaGateway()
