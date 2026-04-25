GEMINI_MODELS = ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-flash"]
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama3-8b-8192"]


def get_models_by_provider(provider: str):
    if "Gemini" in provider:
        return GEMINI_MODELS
    elif "Groq" in provider:
        return GROQ_MODELS
    elif "OpenAI" in provider:
        return OPENAI_MODELS
    return []