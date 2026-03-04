import openai


class AIEngine:

    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = api_key

    def generate_hook(self, title):

        prompt = f"""
        Create a viral hook for this video:
        {title}

        Make it short, engaging, social-media ready.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response["choices"][0]["message"]["content"].strip()

    def analyze_niche(self, title):

        prompt = f"""
        Analyze niche and target audience for:
        {title}

        Return short summary and 5 hashtags.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response["choices"][0]["message"]["content"].strip()

    def generate_subtitle(self, title):

        prompt = f"""
        Create short subtitle caption for:
        {title}

        Make it natural, emotional, short.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response["choices"][0]["message"]["content"].strip()