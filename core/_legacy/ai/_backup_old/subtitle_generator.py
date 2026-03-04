import openai
import os


class SubtitleGenerator:

    def __init__(self, api_key):
        openai.api_key = api_key

    def generate_subtitles(self, audio_path):

        with open(audio_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )

        return transcript["text"]