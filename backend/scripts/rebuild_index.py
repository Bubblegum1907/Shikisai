import pandas as pd
import numpy as np
import faiss
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "my_tracks_with_clap.csv"
INDEX_PATH = ROOT / "data" / "faiss.index"

def rebuild_index():
    print("Rebuilding Affective FAISS Index...")
    if not CSV_PATH.exists():
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    valid_embeddings = []
    valid_v_dims = []
    skipped_count = 0
    
    print("Validating and parsing embeddings...")
    for idx, row in df.iterrows():
        try:
            # Safely parse the embedding string back to a list
            emb = eval(row['clap_embed'])
            
            # Ensure it's a list/array and NOT empty (e.g., skip '[]' or malformed data)
            if isinstance(emb, list) and len(emb) > 0:
                valid_embeddings.append(emb)
                valid_v_dims.append([float(row['valence']), float(row['energy'])])
            else:
                skipped_count += 1
        except Exception:
            skipped_count += 1

    if skipped_count > 0:
        print(f"⚠️ Warning: Skipped {skipped_count} rows with empty or corrupt embeddings.")

    if not valid_embeddings:
        print("❌ Error: No valid embeddings found to build the FAISS index!")
        return

    # Convert to pure float32 numpy arrays
    embeddings = np.array(valid_embeddings, dtype='float32')
    v_dims = np.array(valid_v_dims, dtype='float32')
    
    # Horizontally stack features: [CLAP Embedding (e.g., 512) + Valence (1) + Energy (1)]
    combined_vectors = np.hstack((embeddings, v_dims))
    
    d = combined_vectors.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(combined_vectors)
    
    faiss.write_index(index, str(INDEX_PATH))
    print(f"✅ Success: Index rebuilt with {len(valid_embeddings)} vectors (Dim: {d})")
    print(f"Saved to: {INDEX_PATH}")

if __name__ == "__main__":
    rebuild_index()