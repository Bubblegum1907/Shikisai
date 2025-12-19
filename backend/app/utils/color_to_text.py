# app/utils/color_to_text.py
import json
import os

# Load JSON once
JSON_PATH = os.path.join(os.path.dirname(__file__), "../static/colors_to_feelings.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    COLOR_FEELINGS = json.load(f)


def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def closest_color(hex_color):
    """Find the closest color in the JSON by RGB distance."""
    target = hex_to_rgb(hex_color)
    best = None
    best_dist = float("inf")

    for color_hex in COLOR_FEELINGS.keys():
        rgb = hex_to_rgb(color_hex)
        dist = sum((target[i] - rgb[i])**2 for i in range(3))

        if dist < best_dist:
            best_dist = dist
            best = color_hex

    return best


def color_to_emotion(hex_color):
    """Return emotion string from JSON or nearest-matching color."""
    hex_clean = hex_color.strip().lower()

    if not hex_clean.startswith("#"):
        hex_clean = "#" + hex_clean

    if hex_clean in COLOR_FEELINGS:
        return COLOR_FEELINGS[hex_clean]

    nearest = closest_color(hex_clean)
    return COLOR_FEELINGS.get(nearest, "neutral, calm")


def color_to_text_prompt(hex_color):
    """
    Create the text prompt used to generate CLAP embeddings.
    Returns: (prompt_text, emotion_string)
    """
    emotions = color_to_emotion(hex_color)

    prompt = (
        f"This color conveys emotional qualities of {emotions}. "
        f"Based on color psychology, it expresses feelings such as {emotions}. "
        f"The atmosphere of this color can be described as {emotions}."
    )

    return prompt, emotions
