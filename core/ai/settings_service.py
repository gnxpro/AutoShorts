from core.settings_store import load_config, save_config, get as cfg_get, set as cfg_set

def get_ai_settings():
    cfg = load_config()
    return {
        "provider": cfg_get(cfg, "ai.provider", "Gemini AI"),
        "model": cfg_get(cfg, "ai.model", "gemini-2.0-flash"),
        "api_key": cfg_get(cfg, "ai.api_key", "")
    }

def save_ai_settings(provider, model, api_key):
    cfg = load_config()
    cfg_set(cfg, "ai.provider", provider)
    cfg_set(cfg, "ai.model", model)
    cfg_set(cfg, "ai.api_key", api_key)
    save_config(cfg)