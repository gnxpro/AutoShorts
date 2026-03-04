from core.ai.openai_client import OpenAIClient


class HookService:

    def __init__(self, api_key):
        self.client = OpenAIClient(api_key)

    def generate_hooks(self, title):
        system_prompt = "Generate 5 short viral hook captions for YouTube Shorts."
        return self.client.chat(
            model="gpt-4o-mini",
            system_prompt=system_prompt,
            user_input=title
        )
