from .prompt_templates import hashtag_prompt


class HashtagEngine:

    def __init__(self, client, model):
        self.client = client
        self.model = model

    async def generate(self, topic, platform, language):
        prompt = hashtag_prompt(topic, platform, language)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You generate platform-optimized hashtags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=150
        )

        return response.choices[0].message.content.strip()