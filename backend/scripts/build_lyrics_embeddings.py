import sys
import os
import json
from dotenv import load_dotenv
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.utils.clap_encoder import ClapEncoder
from app.utils.lyrics_embedder import LyricsEmbedder

def main():
    env_path = os.path.join(BACKEND_DIR, ".env")
    load_dotenv(dotenv_path=env_path)

    print("--- System Check ---")
    SONGS_PATH = os.path.join(BACKEND_DIR, "data", "song_metadata.json")
    
    if not os.path.exists(SONGS_PATH):
        print(f"Metadata Missing: {SONGS_PATH}")
        return

    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        print(f"Genius Token Missing! Checked: {env_path}")
        return
    else:
        print(f"Genius Token Loaded: {token[:4]}***")
    print("--------------------\n")

    with open(SONGS_PATH, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print("Initializing Encoders (this may take a moment)...")
    clap = ClapEncoder()
    embedder = LyricsEmbedder(clap)

    count = 0
    print(f"Starting process for {len(songs)} songs...\n")

    for s in songs:
        # 1. Use 'name' if 'title' is missing (Spotify call it 'name')
        title = s.get("name") or s.get("title") 
        artists = s.get("artists", [])
        
        if not title or not artists:
            continue

        artist = artists if isinstance(artists, str) else artists[0]
        
        time.sleep(0.1)
        
        # 2. Get the embedding
        emb = embedder.embed_song(title, artist)

        if emb is not None:
            # 3. CRITICAL: Save the embedding into the song dictionary!
            s["clap_embed"] = emb.tolist() if hasattr(emb, 'tolist') else emb
            count += 1
            print(f"  [SUCCESS] {title} - {artist}")
        else:
            print(f"  [SKIPPED] {title} - {artist}")

    # 4. CRITICAL: Save the updated 'songs' list back to the JSON file
    with open(SONGS_PATH, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    print(f"\nDone! New embeddings saved. Total: {count}/{len(songs)}")

if __name__ == "__main__":
    main()