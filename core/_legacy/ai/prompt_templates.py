def hook_prompt(title, tone, style):
    return f"""
Create a short viral hook for this video:

Title: {title}

Tone: {tone}
Style: {style}

Make it powerful, scroll-stopping, max 1 sentence.
"""


def niche_prompt(description):
    return f"""
Analyze this content:

{description}

Return:
- Niche
- Target audience
- Suggested angle
- Suggested CTA
"""


def hashtag_prompt(topic, platform, language):
    return f"""
Generate optimized hashtags.

Topic: {topic}
Platform: {platform}
Language: {language}

Return 10-15 hashtags optimized for algorithm.
"""


def subtitle_prompt(transcript, style):
    return f"""
Format this transcript for {style} subtitle style.

Transcript:
{transcript}

Make it punchy and readable.
"""