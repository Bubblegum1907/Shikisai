# app/utils/color_to_text.py
import json
import os

JSON_PATH = os.path.join(os.path.dirname(__file__), "../static/colors_to_feelings.json")
with open(JSON_PATH, "r", encoding="utf-8") as f:
    COLOR_FEELINGS = json.load(f)

# EXTREME VAD ANCHORS: We push these to the edges to force FAISS separation
VAD_ANCHORS = {
    "red": (0.25, 0.98),     # High Arousal, Low-Mid Valence (Aggressive/Intense)
    "neon green": (0.90, 0.85), # High Arousal, High Valence (Electric/Energetic)
    "lavender": (0.85, 0.15),   # Low Arousal, High Valence (Dreamy/Peaceful)
    "blue": (0.70, 0.20),    # Low Arousal, High Valence (Stable/Cool)
    "black": (0.10, 0.40),   # Low Valence, Mid Arousal (Dark/Heavy)
}

def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def closest_color(hex_color):
    target = hex_to_rgb(hex_color)
    best, best_dist = None, float("inf")
    for color_hex in COLOR_FEELINGS.keys():
        rgb = hex_to_rgb(color_hex)
        dist = sum((target[i] - rgb[i])**2 for i in range(3))
        if dist < best_dist:
            best_dist, best = dist, color_hex
    return best

def color_to_text_prompt(hex_color):
    hex_clean = hex_color.strip().lower()
    if not hex_clean.startswith("#"): hex_clean = "#" + hex_clean

    # Get raw emotions from JSON
    if hex_clean in COLOR_FEELINGS:
        emotions = COLOR_FEELINGS[hex_clean]
    else:
        nearest = closest_color(hex_clean)
        emotions = COLOR_FEELINGS.get(nearest, "neutral vibe")

    # Determine VAD based on color name keywords
    v, a = 0.5, 0.5
    for key, val in VAD_ANCHORS.items():
        if key in emotions.lower() or key in hex_clean:
            v, a = val
            break

    # LAYERED PROMPT ARCHITECTURE:
    # We change the vocabulary entirely based on Arousal levels
    if a > 0.8:
        # High Arousal (Red, Neon)
        style = "Aggressive electronic synthesizers, high-tempo distorted beats, and intense energy."
        scene = "A high-octane, fast-moving cinematic chase sequence."
    elif a < 0.3:
        # Low Arousal (Lavender, Soft Blue)
        style = "Minimalist ambient piano, soft reverb-drenched pads, and slow tempo."
        scene = "A motionless, ethereal landscape under a quiet moonlit sky."
    else:
        # Mid Arousal
        style = "Rhythmic acoustic instrumentation with steady melodic progression."
        scene = "A balanced and focused environment."

    prompt = (
        f"A professional audio recording featuring {style} "
        f"This music captures a mood that is {emotions}. "
        f"The sonic texture evokes a sense of {scene} "
        f"Specifically tailored to represent the visual frequency of {hex_clean}."
    )

    return prompt, (v, a)