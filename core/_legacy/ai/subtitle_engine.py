from .prompt_templates import subtitle_prompt


class SubtitleEngine:

    def __init__(self, client, model):
        self.client = client
        self.model = model

    async def format(self, transcript, style):
        prompt = subtitle_prompt(transcript, style)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You format subtitles for short-form video."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()