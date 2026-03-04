import random


def format_for_platform(platform: str, hook: str, caption: str, cta: str, hashtags: list, duration: int):

    platform = platform.lower()

    if platform == "tiktok":
        return _format_tiktok(hook, caption, cta, hashtags)

    if platform == "instagram":
        return _format_instagram(hook, caption, cta, hashtags, duration)

    if platform == "youtube":
        return _format_youtube(hook, caption, cta, hashtags)

    return {
        "caption": caption,
        "hashtags": hashtags
    }


# ==========================================================
# TIKTOK
# ==========================================================

def _format_tiktok(hook, caption, cta, hashtags):

    base_tags = hashtags[:5]
    base_tags += ["fyp", "foryou"]

    tag_string = " ".join([f"#{t.replace(' ', '')}" for t in base_tags])

    final_caption = f"{hook}\n\n{caption}\n\n{cta}\n\n{tag_string}"

    return {
        "caption": final_caption,
        "hashtags": base_tags
    }


# ==========================================================
# INSTAGRAM
# ==========================================================

def _format_instagram(hook, caption, cta, hashtags, duration):

    base_tags = hashtags[:10]
    base_tags += ["reels", "reelsindonesia"]

    tag_string = " ".join([f"#{t.replace(' ', '')}" for t in base_tags])

    if duration > 120:
        caption_body = f"{caption}\n\nDetail lengkap ada di video 👇"
    else:
        caption_body = caption

    final_caption = f"{hook}\n\n{caption_body}\n\n{cta}\n\n{tag_string}"

    return {
        "caption": final_caption,
        "hashtags": base_tags
    }


# ==========================================================
# YOUTUBE
# ==========================================================

def _format_youtube(hook, caption, cta, hashtags):

    tags = hashtags[:12]

    final_caption = f"{hook}\n\n{caption}\n\n{cta}"

    return {
        "caption": final_caption,
        "tags": tags
    }