import requests


class OpenAIClient:

    def __init__(self, api_key):
        self.api_key = api_key

    def chat(self, model, system_prompt, user_input):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
