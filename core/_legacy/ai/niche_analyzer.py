from .prompt_templates import niche_prompt


class NicheAnalyzer:

    def __init__(self, client, model):
        self.client = client
        self.model = model

    async def analyze(self, description):
        prompt = niche_prompt(description)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a niche analysis expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()