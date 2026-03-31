import os
import pandas as pd
from .color_utils import hex_to_lab

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PALETTE_PATH = os.path.join(DATA_DIR, "colors and feelings.xlsx")

EMOTION_VAD_MAP = {
    "energetic": {"v": 0.8, "a": 0.9},
    "passionate": {"v": 0.9, "a": 0.8},
    "bold": {"v": 0.6, "a": 0.8},
    "vibrant": {"v": 0.8, "a": 0.8},
    "lively": {"v": 0.8, "a": 0.7},
    "playful": {"v": 0.8, "a": 0.6},
    "uplifting": {"v": 0.9, "a": 0.6},
    "joyful": {"v": 1.0, "a": 0.7},
    "happy": {"v": 0.9, "a": 0.6},
    "confident": {"v": 0.7, "a": 0.7},

    "intense": {"v": 0.4, "a": 0.9},
    "fiery": {"v": 0.5, "a": 0.9},
    "urgent": {"v": 0.3, "a": 0.9},
    "dominant": {"v": 0.4, "a": 0.8},
    "powerful": {"v": 0.5, "a": 0.8},
    "fierce": {"v": 0.3, "a": 0.8},
    "aggressive": {"v": 0.2, "a": 0.9},
    "brooding": {"v": 0.2, "a": 0.6},
    "dramatic": {"v": 0.4, "a": 0.7},
    "commanding": {"v": 0.5, "a": 0.7},

    "calm": {"v": 0.7, "a": 0.2},
    "serene": {"v": 0.8, "a": 0.1},
    "peaceful": {"v": 0.9, "a": 0.1},
    "gentle": {"v": 0.7, "a": 0.2},
    "soft": {"v": 0.6, "a": 0.3},
    "airy": {"v": 0.8, "a": 0.2},
    "soothing": {"v": 0.8, "a": 0.2},
    "dreamy": {"v": 0.7, "a": 0.3},
    "tender": {"v": 0.8, "a": 0.3},

    "serious": {"v": 0.4, "a": 0.4},
    "grounded": {"v": 0.5, "a": 0.3},
    "stable": {"v": 0.6, "a": 0.3},
    "focused": {"v": 0.6, "a": 0.5},
    "introspective": {"v": 0.4, "a": 0.3},
    "contemplative": {"v": 0.4, "a": 0.2},
    "mysterious": {"v": 0.3, "a": 0.5},
    "dark": {"v": 0.1, "a": 0.5},
    "heavy": {"v": 0.2, "a": 0.6},
}

def get_vad(e1, e2):
    v1 = EMOTION_VAD_MAP.get(str(e1).lower(), {"v": 0.5, "a": 0.5})
    v2 = EMOTION_VAD_MAP.get(str(e2).lower(), {"v": 0.5, "a": 0.5})
    return {
        "valence": (v1["v"] + v2["v"]) / 2,
        "arousal": (v1["a"] + v2["a"]) / 2
    }

def load_palette():
    """Load and clean the Excel palette file."""
    if not os.path.isfile(PALETTE_PATH):
        print(f"CRITICAL: Excel file NOT found at: {PALETTE_PATH}")
        return []
    
    df = pd.read_excel(PALETTE_PATH)

    cleaned = []
    for _, row in df.iterrows():
        hex_code = str(row.get('hex', '')).strip().upper()
        if not hex_code.startswith('#'):
            hex_code = f"#{hex_code}"
        e1 = str(row.get('emotion1', '')).strip()
        e2 = str(row.get('emotion2', '')).strip()
        name = str(row.get('name', '')).strip()

        lab_value = hex_to_lab(hex_code)
        
        vad_values = get_vad(e1, e2)

        cleaned.append({
            "name": name,
            "emotion1": e1,
            "emotion2": e2,
            "hex": hex_code,
            "lab": lab_value or (50, 0, 0),
            "vad": vad_values
        })

    return cleaned