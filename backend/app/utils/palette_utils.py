import json
import os
from .color_utils import hex_to_lab

# Go up THREE levels: utils -> app -> backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PALETTE_PATH = os.path.join(DATA_DIR, "colors and feelings.json")

def load_palette():
    """Load and clean the palette file."""
    if not os.path.isfile(PALETTE_PATH):
        raise FileNotFoundError(f"Palette file not found at: {PALETTE_PATH}")

    with open(PALETTE_PATH, "r", encoding="utf-8") as f:
        raw_palette = json.load(f)

    cleaned = []
    for c in raw_palette:

        name = (c.get("name") or "").strip()
        e1 = (c.get("emotion1") or "").strip()
        e2 = (c.get("emotion2") or "").strip()
        hex_code = (c.get("hex") or "").strip()

        # Convert hex -> LAB
        lab_value = hex_to_lab(hex_code)
        if lab_value is None:
            lab_value = (50, 0, 0)  # fallback

        cleaned.append({
            "name": name,
            "emotion1": e1,
            "emotion2": e2,
            "hex": hex_code,
            "lab": lab_value
        })

    return cleaned
