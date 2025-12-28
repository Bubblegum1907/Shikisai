# app/utils/emotion_utils.py
import numpy as np

# Mini VAD dictionary
VAD_MAP = {
    "anger": (0.2, 0.9, 0.6),
    "aggressive": (0.1, 0.9, 0.7),
    "passionate": (0.7, 0.8, 0.7),
    "intense": (0.4, 0.9, 0.6),
    "sad": (0.2, 0.2, 0.3),
    "calm": (0.7, 0.2, 0.6),
    "peaceful": (0.8, 0.2, 0.6),
    "happy": (0.9, 0.6, 0.5),
    "joyful": (0.95, 0.7, 0.5),
    "energetic": (0.6, 0.9, 0.6),
    "vibrant": (0.7, 0.9, 0.6),
    "romantic": (0.8, 0.5, 0.5),
    "dreamy": (0.6, 0.3, 0.4),
    "mysterious": (0.3, 0.3, 0.6),
    "bright": (0.85, 0.7, 0.5),
    "fresh": (0.75, 0.4, 0.5),
    "warm": (0.7, 0.4, 0.6),
    "grounded": (0.5, 0.3, 0.7),
    "neutral": (0.5, 0.4, 0.5)
}


def emotions_to_vad(emotion_string: str):
    """
    Convert emotion text (e.g. "warm, energetic") to a 3-value VAD vector.
    We average any known emotions found in the VAD_MAP.
    """
    words = [w.strip().lower() for w in emotion_string.replace("/", ",").split(",")]
    vad = np.zeros(3, dtype=np.float32)
    count = 0

    for w in words:
        if w in VAD_MAP:
            vad += np.array(VAD_MAP[w], dtype=np.float32)
            count += 1

    if count == 0:
        return np.array(VAD_MAP["neutral"], dtype=np.float32)

    return vad / count
