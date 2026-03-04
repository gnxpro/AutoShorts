from .prompt_templates import hook_prompt


class HookGenerator:

    def __init__(self, client, model):
        self.client = client
        self.model = model

    async def generate(self, title, tone, style):
        prompt = hook_prompt(title, tone, style)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a viral content strategist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=120
        )

        return response.choices[0].message.content.strip()