"""Ollama client for Xuehua - handles embeddings and chat via Ollama API."""

from __future__ import annotations

import json
import logging
import sys
from typing import Dict, Iterator, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama API supporting embeddings and chat."""

    EMBEDDING_PATTERNS = [
        "nomic-embed",
        "bge-m3",
        "bge-large",
        "bge-base",
        "bge-small",
        "mxbai-embed",
        "all-minilm",
        "snowflake-arctic-embed",
        "multilingual-e5",
        "e5-large",
        "e5-base",
        "e5-small",
        "gte-large",
        "gte-base",
        "gte-small",
        "gte-qwen",
        "jina-embed",
        "paraphrase",
        "sentence-t5",
        "instructor",
        "text-embedding",
        "embed",
        "embedding",
    ]

    def __init__(self, api_url: str = "http://localhost:11434"):
        self.api_url = api_url.rstrip("/")
        self._session = requests.Session()
        retry = Retry(
            total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
        self._session.mount("http://", HTTPAdapter(max_retries=retry))
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._stop_flag = False
        self._context_length = 4096

    def set_context_length(self, length: int):
        self._context_length = max(512, min(length, 1000000))

    def get_context_length(self) -> int:
        return self._context_length

    def is_available(self) -> bool:
        try:
            r = self._session.get(f"{self.api_url}/api/tags", timeout=5)
            return r.status_code == 200
        except (requests.RequestException, requests.Timeout):
            return False

    def get_models(self) -> List[str]:
        try:
            r = self._session.get(f"{self.api_url}/api/tags", timeout=30)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def get_embedding_models(self) -> List[str]:
        models = self.get_models()
        result = []
        for pattern in self.EMBEDDING_PATTERNS:
            for m in models:
                if pattern in m.lower() and m not in result:
                    result.append(m)
        return result

    def get_chat_models(self) -> List[str]:
        models = self.get_models()
        return [
            m for m in models
            if not any(p in m.lower() for p in self.EMBEDDING_PATTERNS)
        ]

    def embed(self, text: str, model: str) -> List[float]:
        text = text[:500] if len(text) > 500 else text
        r = self._session.post(
            f"{self.api_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=60,
        )
        r.raise_for_status()
        return r.json().get("embedding", [])

    def chat_complete(
        self,
        messages: List[Dict],
        model: str,
        temperature: float = 0.7,
        num_ctx: int = None,
    ) -> str:
        ctx_len = num_ctx or self._context_length
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": ctx_len},
        }
        try:
            r = self._session.post(
                f"{self.api_url}/api/chat", json=payload, timeout=300
            )
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error("[Ollama] chat_complete error: %s", e)
            return ""

    def chat_stream(
        self,
        messages: List[Dict],
        model: str,
        temperature: float = 0.7,
        num_ctx: int = None,
    ) -> Iterator[str]:
        self._stop_flag = False
        ctx_len = num_ctx or self._context_length
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature, "num_ctx": ctx_len},
        }
        try:
            r = self._session.post(
                f"{self.api_url}/api/chat", json=payload, stream=True, timeout=300
            )
            r.raise_for_status()
            for line in r.iter_lines():
                if self._stop_flag:
                    r.close()
                    break
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield f"\n\n[Error: {e}]"

    def stop_generation(self):
        self._stop_flag = True

    def reset_stop(self):
        self._stop_flag = False