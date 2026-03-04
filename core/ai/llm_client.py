# core/ai/llm_client.py
from __future__ import annotations

import json
import time
import os
from typing import Optional, Any, Dict


class LLMClientError(RuntimeError):
    pass


class OpenAIClient:
    """
    Production-grade OpenAI wrapper (safe for PyInstaller).

    Key features:
    - Lazy import (no crash if openai package is missing in non-AI plans/builds)
    - JSON enforcement
    - Retry mechanism
    - Token & temperature control
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 1200,
        temperature: float = 0.7,
        timeout: int = 60,
        max_retries: int = 2,
    ):
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = model
        self.max_tokens = int(max_tokens)
        self.temperature = float(temperature)
        self.timeout = int(timeout)
        self.max_retries = int(max_retries)

        self._client = None  # lazy init

    # ==========================================================
    # Internal: lazy client
    # ==========================================================
    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY is not set. Please save your key in AI Settings.")

        # ✅ Lazy import: do NOT crash app at startup
        try:
            from openai import OpenAI  # new SDK
            self._client = OpenAI(api_key=self.api_key)
            return self._client
        except Exception:
            # fallback: old SDK style
            try:
                import openai  # type: ignore
                openai.api_key = self.api_key
                self._client = openai
                return self._client
            except ModuleNotFoundError:
                raise LLMClientError(
                    "OpenAI library is not installed in this build. "
                    "Install 'openai' and rebuild Premium installer."
                )

    # ==========================================================
    # PUBLIC CALL
    # ==========================================================
    def generate(self, prompt: str) -> str:
        """
        Returns raw JSON string.
        Retries if output is not valid JSON.
        """
        attempt = 0
        last_err = None

        while attempt <= self.max_retries:
            try:
                client = self._get_client()

                # New SDK path: client.chat.completions.create(...)
                if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                    resp = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a precise JSON generator. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        response_format={"type": "json_object"},
                        timeout=self.timeout,
                    )
                    content = resp.choices[0].message.content.strip()

                # Old SDK fallback: openai.ChatCompletion.create(...)
                else:
                    resp = client.ChatCompletion.create(  # type: ignore
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a precise JSON generator. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )
                    content = resp["choices"][0]["message"]["content"].strip()

                # Validate JSON
                json.loads(content)
                return content

            except Exception as e:
                last_err = e
                attempt += 1
                time.sleep(1)

        raise LLMClientError(f"GPT generation failed after retries: {last_err}")