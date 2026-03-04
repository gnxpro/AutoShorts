# core/ai/provider_router.py
from __future__ import annotations

import os
from typing import Any, Optional


class ProviderNotAvailableError(RuntimeError):
    pass


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


class ProviderRouter:
    """
    Lazy import providers so the app won't crash if a provider library is missing.
    - Premium build: include openai so AI works.
    - Free/Basic plan: AI can be disabled and app still runs without openai.
    """

    def __init__(self):
        self.default_provider = _env("AI_PROVIDER", "openai").lower()

    def get_provider_name(self) -> str:
        return self.default_provider

    def get_client(self, provider: Optional[str] = None) -> Any:
        provider = (provider or self.default_provider or "openai").lower()

        if provider == "openai":
            return self._get_openai_client()

        raise ProviderNotAvailableError(f"Unknown AI provider: {provider}")

    # --------------------------
    # OpenAI
    # --------------------------
    def _get_openai_client(self) -> Any:
        api_key = _env("OPENAI_API_KEY")
        if not api_key:
            # Do NOT crash whole app. Raise a clear message for the caller/UI.
            raise ProviderNotAvailableError(
                "OPENAI_API_KEY is not set. Go to AI Settings and save your key."
            )

        # ✅ Lazy import: no ModuleNotFoundError at app startup
        try:
            # New OpenAI Python SDK (recommended): from openai import OpenAI
            from openai import OpenAI  # type: ignore
            return OpenAI(api_key=api_key)
        except Exception:
            # Fallback: old SDK import style
            try:
                import openai  # type: ignore
                openai.api_key = api_key
                return openai
            except ModuleNotFoundError:
                raise ProviderNotAvailableError(
                    "OpenAI library is not installed in this build. "
                    "Install 'openai' and rebuild the Premium installer."
                )