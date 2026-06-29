import pandas as pd
import numpy as np
import json
from pathlib import Path

# Fix folder paths cleanly relative to this script
SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR.parent / "data"

CSV_PATH = DATA_DIR / "my_tracks_with_clap.csv"
META_OUT = DATA_DIR / "song_metadata.json"
VEC_OUT = DATA_DIR / "song_vectors.npy"

def main():
    print("🚀 Starting direct compilation of SongStore records...")
    
    if not CSV_PATH.exists():
        print(f"❌ Error: Could not find your CSV at {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"📋 Reading {len(df)} tracks from CSV...")

    meta_entries = []
    vector_list = []
    skipped_count = 0

    for idx, row in df.iterrows():
        try:
            # 1. Parse and validate the CLAP embedding list safely
            clap_val = row.get("clap_embed", "[]")
            emb = eval(clap_val) if isinstance(clap_val, str) else clap_val
            
            # Ensure it is a valid list
            if not isinstance(emb, list) or len(emb) == 0:
                # Fallback to zeros matching standard 515 dimensions
                emb = [0.0] * 515
            elif len(emb) != 515:
                # Pad or slice cleanly to exactly 515 dimensions
                emb = emb[:515] + [0.0] * max(0, 515 - len(emb))
                
            # 2. Extract metrics for metadata
            v = float(row.get("valence", 0.5))
            a = float(row.get("energy", 0.5)) # Energy maps directly to arousal
            d = float(row.get("dominance", 0.5)) # Fallback default

            # 3. Use the 515-dimensional vector directly
            combined_vec = np.array(emb, dtype=np.float32) # Exactly 515 dimensions
            vector_list.append(combined_vec)

            # 4. Reconstruct metadata dictionary layout
            artists_raw = row.get("artists", "Unknown")
            artists_list = [a.strip() for a in str(artists_raw).split(",")] if "," in str(artists_raw) else [str(artists_raw)]
            
            genres_raw = row.get("genres", "[]")
            genres_list = eval(genres_raw) if isinstance(genres_raw, str) else []

            meta_item = {
                "spotify_id": str(row["id"]),
                "name": str(row["name"]),
                "artists": artists_list,
                "genres": genres_list,
                "vad_score": [v, a, d],
                "preview_url": str(row.get("preview_url", "")) if pd.notna(row.get("preview_url")) else None
            }
            meta_entries.append(meta_item)

        except Exception as e:
            skipped_count += 1
            continue

    if skipped_count > 0:
        print(f"⚠️ Skipped {skipped_count} malformed rows.")

    if not vector_list:
        print("❌ Error: No vectors were compiled. Aborting.")
        return

    # Convert to numpy block matrix
    final_vectors = np.stack(vector_list).astype(np.float32)

    # Write files exactly where SongStore expects to read them
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta_entries, f, indent=2, ensure_ascii=False)
        
    np.save(VEC_OUT, final_vectors)

    print("\n✨ Data Generation Complete!")
    print(f"📁 song_metadata.json -> Saved {len(meta_entries)} items.")
    print(f"📁 song_vectors.npy   -> Saved matrix with shape {final_vectors.shape}")

if __name__ == "__main__":
    main()