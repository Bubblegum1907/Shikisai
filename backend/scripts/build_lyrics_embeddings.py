import sys
import os
import json
from dotenv import load_dotenv

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
        print(f"❌ Metadata Missing: {SONGS_PATH}")
        return
    else:
        print(f"✅ Metadata Found: {SONGS_PATH}")

    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        print(f"❌ Genius Token Missing! Checked: {env_path}")
        return
    else:
        print(f"✅ Genius Token Loaded: {token[:4]}***")
    print("--------------------\n")

    with open(SONGS_PATH, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print("Initializing Encoders (this may take a moment)...")
    clap = ClapEncoder()
    embedder = LyricsEmbedder(clap)

    count = 0
    print(f"Starting process for {len(songs)} songs...\n")

    for s in songs:
        title = s.get("title")
        artists = s.get("artists", [])
        if isinstance(artists, str):
            artists = [artists]
            
        if not title or not artists:
            continue

        artist = artists[0]
        
        emb = embedder.embed_song(title, artist)

        if emb is not None:
            count += 1
            print(f"  [SUCCESS] {title} - {artist}")
        else:
            print(f"  [SKIPPED] {title} - {artist}")

    print(f"\n✨ Done! New embeddings saved. Total: {count}/{len(songs)}")

if __name__ == "__main__":
    main()