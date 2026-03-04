from core.config_manager import load_config


def generate_ai_metadata(title, niche, manual_prompt=None):

    config = load_config()

    if config.get("ai_provider") != "openai":
        return {
            "title": title,
            "description": f"{title} #shorts",
            "hashtags": "#shorts"
        }

    api_key = config.get("openai_api_key")

    if not api_key:
        return {
            "title": title,
            "description": f"{title} #shorts",
            "hashtags": "#shorts"
        }

    try:
        import openai
        openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Create viral metadata for {title}"}
            ]
        )

        text = response["choices"][0]["message"]["content"]

        return {
            "title": title,
            "description": text,
            "hashtags": "#shorts #viral"
        }

    except:
        return {
            "title": title,
            "description": f"{title} #shorts",
            "hashtags": "#shorts"
        }