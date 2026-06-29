import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] 
BACKEND = ROOT / "backend"
DATA_DIR = BACKEND / "data"

# THE SOURCE FILES
SNG_META = DATA_DIR / "song_metadata.json"
SNG_VEC  = DATA_DIR / "song_vectors.npy" 
OUT_CSV  = DATA_DIR / "my_tracks_with_clap.csv"

def main():
    print(f"--- IBA_OS: The Great Reunion (Fixed) ---")

    if not SNG_META.exists() or not SNG_VEC.exists():
        print(f"❌ Error: Missing files!")
        return

    with open(SNG_META, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    songs = list(meta_data.values()) if isinstance(meta_data, dict) else meta_data

    vectors = np.load(SNG_VEC)
    
    print(f"Loaded {len(songs)} metadata records and {len(vectors)} vectors.")
    print(f"Vector shape detected: {vectors.shape}")

    count = min(len(songs), len(vectors))
    rows = []

    for i in range(count):
        s = songs[i]
        raw_vec = vectors[i]
        
        # Smart Slicing: Check if vectors already contain appended VAD metrics (515 dimensions)
        if raw_vec.shape[0] == 515:
            base_vec = raw_vec[:512].tolist()  # Keep only pure CLAP embedding in the text slot
            vad = raw_vec[-3:].tolist()        # Pull true computed VAD from the tail
        else:
            base_vec = raw_vec.tolist()
            # Fall back to metadata dictionary or standard neutral coordinates
            vad = s.get("vad_score") or [0.5, 0.5, 0.5]

        raw_artists = s.get("artists", "Unknown")
        if isinstance(raw_artists, list):
            artists_str = ", ".join(raw_artists)
        else:
            artists_str = str(raw_artists)

        rows.append({
            "id": s.get("spotify_id") or f"track_{i}",
            "name": s.get("title") or "Unknown",
            "artists": artists_str, 
            "genres": s.get("genres") or [],
            "clap_embed": json.dumps(base_vec), 
            "valence": float(vad[0]),
            "energy": float(vad[1]),     # Maps neatly to Arousal
            "dominance": float(vad[2]),  # Preserves emotional posture/power axis
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    
    print(f"✅ SUCCESS: {len(df)} tracks unified into {OUT_CSV}")

if __name__ == "__main__":
    main()