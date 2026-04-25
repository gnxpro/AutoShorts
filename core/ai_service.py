from google import genai
from openai import OpenAI
from groq import Groq  # Library yang baru saja Abang instal
from core.settings_store import load_config, get as cfg_get

class AIService:
    def __init__(self):
        self.refresh_config()

    def refresh_config(self):
        self.cfg = load_config()
        self.provider = cfg_get(self.cfg, "ai.provider", "OFF")
        self.model_name = cfg_get(self.cfg, "ai.model", "gemini-2.0-flash")
        self.api_key = cfg_get(self.cfg, "ai.api_key", "")

    def is_enabled(self):
        return "OFF" not in self.provider and bool(self.api_key)

    def generate_viral_content(self, topic_or_filename, custom_prompt=""):
        self.refresh_config()
        if not self.is_enabled():
            return {"title": f"Video {topic_or_filename}", "description": "#viral"}

        system_instruction = (
            "You are a professional social media strategist. "
            "Output format strictly:\nTITLE: [Title]\nDESC: [Description]"
        )
        user_message = f"Topic: '{topic_or_filename}'. {custom_prompt}"

        try:
            # 1. LOGIKA UNTUK GROQ (SDK ASLI)
            if "Groq" in self.provider:
                client = Groq(api_key=self.api_key)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_message}
                    ],
                    model=self.model_name,
                )
                return self._parse_ai_response(chat_completion.choices[0].message.content.strip(), topic_or_filename)

            # 2. LOGIKA UNTUK GEMINI
            elif "Gemini" in self.provider:
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model_name,
                    config={'system_instruction': system_instruction},
                    contents=user_message
                )
                return self._parse_ai_response(response.text.strip(), topic_or_filename)

            # 3. LOGIKA UNTUK OPENAI
            elif "OpenAI" in self.provider:
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "system", "content": system_instruction},
                              {"role": "user", "content": user_message}]
                )
                return self._parse_ai_response(response.choices[0].message.content.strip(), topic_or_filename)

        except Exception as e:
            print(f"AI Error: {e}")
            return {"title": f"Auto Post {topic_or_filename}", "description": "#viral"}

    def _parse_ai_response(self, raw_text, fallback_name):
        result = {"title": f"Video - {fallback_name}", "description": "#viral"}
        lines = raw_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith("TITLE:"):
                result["title"] = line[6:].strip()
            elif line.upper().startswith("DESC:"):
                result["description"] = line[5:].strip()
        return result