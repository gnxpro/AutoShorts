import json
from openai import OpenAI
from google import genai  # Correct import statement


class ProviderRouter:

    def __init__(self, config):

        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.7)

        self.openai_client = None
        self.gemini_model = None

        # =============================
        # OPENAI
        # =============================
        if self.provider == "openai":
            api_key = config.get("openai_api_key")

            if not api_key:
                raise Exception("OpenAI API key missing")

            self.openai_client = OpenAI(api_key=api_key)

        # =============================
        # GEMINI
        # =============================
        elif self.provider == "gemini":
            api_key = config.get("gemini_api_key")

            if not api_key:
                raise Exception("Gemini API key missing")

            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-pro")

        else:
            raise Exception(f"Unsupported provider: {self.provider}")

    # =========================================

    def generate(self, system_prompt, user_prompt, model_override=None):

        model_to_use = model_override if model_override else self.model

        if self.provider == "openai":

            response = self.openai_client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature
            )

            return response.choices[0].message.content.strip()

        elif self.provider == "gemini":

            response = self.gemini_model.generate_content(
                f"{system_prompt}\n\n{user_prompt}"
            )

            return response.text.strip()

        else:
            raise Exception("Unsupported provider during generate")