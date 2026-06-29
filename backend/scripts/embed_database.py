import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Fix: Force the root project directory (Shikisai) into Python's search path
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent # Steps back from scripts -> backend -> Shikisai
sys.path.append(str(project_root))

from backend.app.utils.clap_encoder import ClapEncoder
from backend.app.utils.lyrics_embedder import LyricsEmbedder

# Dynamically find paths using Pathlib just like your download script
backend_root = Path(__file__).resolve().parent.parent
csv_path = backend_root / "data" / "my_tracks_with_clap.csv"
audio_dir = backend_root / "data" / "songs"

def embed_entire_database():
    print("🚀 Initializing CLAP models for database-wide batch processing...")
    clap = ClapEncoder()
    embedder = LyricsEmbedder(clap)
    
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found at {csv_path}")
        return

    # Read your tracks database
    df = pd.read_csv(csv_path)
    print(f"📋 Found {len(df)} tracks in CSV to process.")
    
    # Pre-allocate an array or list to store the final vectors if saving back to a new CSV/DB
    generated_vectors = []

    for index, row in df.iterrows():
        track_id = row['id']
        title = row['name']
        artist = row['artists']
        
        print(f"\n[{index + 1}/{len(df)}] Processing: {title} by {artist}")
        
        # --- Modality 1: Lyrics ---
        vector_lyrics = None
        try:
            vector_lyrics = embedder.embed_song(title, artist)
        except Exception as e:
            print(f"❌ Failed to fetch/embed lyrics: {e}")
            
        # --- Modality 2: Audio Snippet ---
        vector_audio = None
        # FIXED: Look for the file using track_id.mp3 matching your downloader script
        audio_path = audio_dir / f"{track_id}.mp3"
        
        if audio_path.exists():
            print(f"➡️ Found 30s snippet ({track_id}.mp3). Encoding audio...")
            vector_audio = clap.encode_audio(str(audio_path))
        else:
            print(f"⚠️ No local audio file found at {audio_path}")
            
        # --- Fusion Step ---
        if vector_lyrics is not None and vector_audio is not None:
            # Combined hybrid representation (515 dimensions)
            final_vector = (0.4 * vector_lyrics) + (0.6 * vector_audio)
        elif vector_lyrics is not None:
            final_vector = vector_lyrics
        elif vector_audio is not None:
            final_vector = vector_audio
        else:
            print(f"⏭️ Skipping {title}: Neither lyrics nor audio could be processed.")
            generated_vectors.append(None)
            continue
            
        # Normalize the vector 
        final_vector = final_vector / (np.linalg.norm(final_vector) + 1e-9)
        
        # Convert to list format
        vector_to_store = final_vector.tolist()
        generated_vectors.append(vector_to_store)
        print(f"✅ Successfully generated 515-dim vector for {title}")

    # Optional: If you want to save them straight back into your CSV as a new column
    # df['vibe_vector'] = generated_vectors
    # df.to_csv(csv_path, index=False)
    # print("\n🎉 Saved all vectors back to CSV!")

if __name__ == "__main__":
    embed_entire_database()