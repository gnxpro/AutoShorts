import re


KEYWORDS = [
    "secret", "crazy", "mistake", "million",
    "important", "never", "truth", "warning",
    "shocking", "insane", "biggest", "why"
]


def score_sentence(text):
    score = 0
    lower = text.lower()

    for k in KEYWORDS:
        if k in lower:
            score += 3

    score += len(text.split()) * 0.2
    return score


def detect_best_hook_from_srt(srt_path):

    best_score = 0
    best_time = 0

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")

    for block in blocks:
        parts = block.split("\n")
        if len(parts) >= 3:

            time_line = parts[1]
            text = " ".join(parts[2:])

            if " --> " not in time_line:
                continue

            start, _ = time_line.split(" --> ")
            score = score_sentence(text)

            if score > best_score:
                best_score = score
                best_time = convert_time_to_seconds(start)

    return best_time


def convert_time_to_seconds(t):
    h, m, s = t.split(":")
    s, ms = s.split(",")
    return int(h)*3600 + int(m)*60 + int(s)