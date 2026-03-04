import json
import time
from typing import Optional

from openai import OpenAI


class OpenAIClient:
    """
    Production-grade GPT-4o wrapper.

    Features:
    - JSON enforcement
    - Retry mechanism
    - Token control
    - Temperature control
    - Credit-safe design
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 1200,
        temperature: float = 0.7,
        timeout: int = 60,
        max_retries: int = 2
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    # ==========================================================
    # PUBLIC CALL
    # ==========================================================

    def generate(self, prompt: str) -> str:
        """
        Returns raw JSON string.
        Retries if output is not valid JSON.
        """

        attempt = 0

        while attempt <= self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise JSON generator. Output ONLY valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                    timeout=self.timeout
                )

                content = response.choices[0].message.content.strip()

                # Validate JSON
                json.loads(content)
                return content

            except Exception as e:
                attempt += 1
                time.sleep(1)

                if attempt > self.max_retries:
                    raise Exception(f"GPT generation failed: {str(e)}")