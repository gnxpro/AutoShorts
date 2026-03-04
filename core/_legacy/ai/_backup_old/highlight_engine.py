from core.ai.openai_client import OpenAIClient


class HighlightEngine:

    def __init__(self, api_key):
        self.client = OpenAIClient(api_key)

    def find_highlights(self, transcript, clip_count):
        system_prompt = (
            f"From this transcript, choose {clip_count} best short highlight segments "
            "with start and end timestamps."
        )

        return self.client.chat(
            model="gpt-4o-mini",
            system_prompt=system_prompt,
            user_input=transcript
        )
