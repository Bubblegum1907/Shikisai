import pandas as pd
import numpy as np
import faiss
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "my_tracks_with_clap.csv"
INDEX_PATH = ROOT / "data" / "faiss.index"

def rebuild_index():
    print("Rebuilding Affective FAISS Index")
    df = pd.read_csv(CSV_PATH)
    
    embeddings = np.array([eval(e) for e in df['clap_embed'].values]).astype('float32')
    
    v_dims = df[['valence', 'energy']].values.astype('float32')
    combined_vectors = np.hstack((embeddings, v_dims))
    
    d = combined_vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(combined_vectors)
    
    faiss.write_index(index, str(INDEX_PATH))
    print(f"Success: Index rebuilt with {len(df)} vectors (Dim: {d})")
    print(f"Saved to: {INDEX_PATH}")

if __name__ == "__main__":
    rebuild_index()