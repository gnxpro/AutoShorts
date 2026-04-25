import requests
import time
from typing import Tuple, Optional


def test_connection(provider: str, api_key: str, model: Optional[str] = None) -> Tuple[bool, str]:
    """
    Test connection to AI provider API.

    Args:
        provider: The AI provider name (e.g., "Gemini AI", "Groq Cloud", "OpenAI")
        api_key: The API key for the provider
        model: The model name (optional, defaults to provider-specific default)

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not api_key:
        return False, "API Key kosong"

    try:
        if "Groq" in provider:
            return _test_groq(api_key, model)

        elif "OpenAI" in provider:
            return _test_openai(api_key, model)

        elif "Gemini" in provider:
            return _test_gemini(api_key, model)

        return False, "Provider tidak dikenali"

    except Exception as e:
        return False, f"Error: {str(e)}"


def _test_groq(api_key: str, model: Optional[str]) -> Tuple[bool, str]:
    """Test Groq API connection."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    return _test_openai_like(url, api_key, model)


def _test_openai(api_key: str, model: Optional[str]) -> Tuple[bool, str]:
    """Test OpenAI API connection."""
    url = "https://api.openai.com/v1/chat/completions"
    return _test_openai_like(url, api_key, model)


def _test_openai_like(url: str, api_key: str, model: Optional[str]) -> Tuple[bool, str]:
    """Test OpenAI-like API (Groq, OpenAI)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model or "gpt-3.5-turbo",  # Default model if None
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 5
    }

    start = time.time()
    res = requests.post(url, headers=headers, json=payload, timeout=15)
    latency = round((time.time() - start) * 1000)

    if res.status_code == 200:
        return True, f"✅ OK ({latency} ms)"
    elif res.status_code == 401:
        return False, "❌ Invalid API Key"
    else:
        return False, f"❌ {res.status_code}"


def _test_gemini(api_key: str, model: Optional[str]) -> Tuple[bool, str]:
    """Test Gemini API connection."""
    model = model or "gemini-2.0-flash"  # Default model if None
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {"parts": [{"text": "Say OK"}]}
        ]
    }

    start = time.time()
    res = requests.post(url, json=payload, timeout=15)
    latency = round((time.time() - start) * 1000)

    if res.status_code == 200:
        return True, f"✅ Gemini OK ({latency} ms)"
    elif res.status_code == 403:
        return False, "❌ API Key invalid / blocked"
    else:
        return False, f"❌ {res.status_code}"

     