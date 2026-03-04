from .smart_router import SmartRouter
from .prompt_templates import (
    hook_prompt,
    niche_prompt,
    hashtag_prompt,
    subtitle_prompt
)


class AIManager:

    def __init__(self, config):
        self.router = SmartRouter(config)

    # =====================================================

    def generate_hook(self, title, tone, style):
        prompt = hook_prompt(title, tone, style)

        return self.router.generate(
            system_prompt="You are a viral content strategist.",
            user_prompt=prompt,
            task_type="hook"
        )

    # =====================================================

    def analyze_niche(self, description):
        prompt = niche_prompt(description)

        return self.router.generate(
            system_prompt="You are a niche analysis expert.",
            user_prompt=prompt,
            task_type="niche"
        )

    # =====================================================

    def generate_hashtags(self, topic, platform, language):
        prompt = hashtag_prompt(topic, platform, language)

        return self.router.generate(
            system_prompt="You generate platform-optimized hashtags.",
            user_prompt=prompt,
            task_type="hashtag"
        )

    # =====================================================

    def generate_subtitle_script(self, transcript, style):
        prompt = subtitle_prompt(transcript, style)

        return self.router.generate(
            system_prompt="You format subtitles for short-form video.",
            user_prompt=prompt,
            task_type="subtitle"
        )