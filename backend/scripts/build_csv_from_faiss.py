# backend/scripts/build_csv_from_faiss.py
import os
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

"""
Build my_tracks_with_clap.csv from:
 - song_metadata.json
 - song_vectors.npy

Output: backend/data/my_tracks_with_clap.csv
"""

ROOT = Path(__file__).resolve().parents[2] 
BACKEND = ROOT / "backend"
DATA_DIR = BACKEND / "data"
SNG_META = BACKEND / "data" / "song_metadata.json"
SNG_VEC = BACKEND / "data" / "song_vectors.npy"
OUT_CSV = DATA_DIR / "my_tracks_with_clap.csv"

def safe_load_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        try:
            keys = sorted(data.keys(), key=lambda k: int(k) if str(k).isdigit() else k)
            return [data[k] for k in keys]
        except Exception:
            return list(data.values())
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unsupported metadata shape in song_metadata.json")

def ensure_fields(meta):
    # return a normalized metadata dict with minimal fields used by recommender
    return {
        "id": meta.get("id") or meta.get("track_id") or meta.get("spotify_id") or meta.get("uri") or meta.get("track_uri") or "",
        "name": meta.get("name") or meta.get("title") or "",
        "artists": meta.get("artists") or meta.get("artist") or meta.get("artists_names") or [],
        "genres": meta.get("genres") or meta.get("genre") or [],
        "popularity": meta.get("popularity") if meta.get("popularity") is not None else meta.get("pop") if meta.get("pop") is not None else 0,
        "release_year": meta.get("release_year") or (meta.get("year") and int(meta.get("year"))) or None,
        "valence": meta.get("valence") if meta.get("valence") is not None else None,
        "energy": meta.get("energy") if meta.get("energy") is not None else None,
        "instrumentalness": meta.get("instrumentalness") if meta.get("instrumentalness") is not None else None,
        "speechiness": meta.get("speechiness") if meta.get("speechiness") is not None else None,
    }

def vector_to_str(vec: np.ndarray):
    return json.dumps(vec.astype(float).tolist(), ensure_ascii=False)

def main():
    print("Project root:", ROOT)
    print("Looking for files:")
    print(" - metadata:", SNG_META)
    print(" - vectors: ", SNG_VEC)
    print("Output CSV:", OUT_CSV)

    if not SNG_META.exists():
        raise FileNotFoundError(f"Missing metadata file: {SNG_META}")
    if not SNG_VEC.exists():
        raise FileNotFoundError(f"Missing vectors file: {SNG_VEC}")

    meta_list = safe_load_metadata(SNG_META)
    print("Metadata entries loaded:", len(meta_list))

    # load vectors
    vectors = np.load(str(SNG_VEC), allow_pickle=False)
    print("Vectors shape:", vectors.shape)

    # If vectors is 1D array of objects, try to stack
    if vectors.ndim == 1 and isinstance(vectors[0], (list, np.ndarray)):
        vectors = np.vstack([np.array(v, dtype=np.float32) for v in vectors])

    # Align lengths
    n_meta = len(meta_list)
    n_vec = vectors.shape[0]
    if n_meta != n_vec:
        print("Warning: metadata length != vectors length.")
        print(" - metadata:", n_meta, "vectors:", n_vec)
        m = min(n_meta, n_vec)
        print(f"Truncating to first {m} entries (best-effort).")
        meta_list = meta_list[:m]
        vectors = vectors[:m]

    # Build dataframe rows
    rows = []
    now_year = datetime.utcnow().year
    for meta, vec in zip(meta_list, vectors):
        nm = ensure_fields(meta)
        # defaults if None
        valence = nm["valence"] if nm["valence"] is not None else 0.5
        energy = nm["energy"] if nm["energy"] is not None else 0.5
        instr = nm["instrumentalness"] if nm["instrumentalness"] is not None else 0.0
        speech = nm["speechiness"] if nm["speechiness"] is not None else 0.05
        pop = nm["popularity"] if nm["popularity"] is not None else 0.0
        year = nm["release_year"] if nm["release_year"] is not None else 2010
        try:
            year = int(year) if year else 2010
        except:
            year = 2010

        row = {
            "id": nm["id"],
            "name": nm["name"],
            "artists": nm["artists"],
            "genres": nm["genres"],
            # Store embedding as a string that literal_eval can parse
            "clap_embed": vector_to_str(np.array(vec, dtype=np.float32)),
            "valence": float(valence),
            "energy": float(energy),
            "instrumentalness": float(instr),
            "speechiness": float(speech),
            "popularity": float(pop),
            "release_year": int(year),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    # ensure data dir exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save CSV
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print("Wrote CSV:", OUT_CSV)
    print("Rows written:", len(df))

    import ast
    sample = df.loc[0, "clap_embed"]
    parsed = ast.literal_eval(sample)
    print("Sample embedding length:", len(parsed))
    print("Done.")

if __name__ == "__main__":
    main()
