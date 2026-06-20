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

    SONGS_PATH = os.path.join(BACKEND_DIR, "data", "song_metadata.json")
    
    if not os.path.exists(SONGS_PATH):
        print(f"Error: {SONGS_PATH} not found.")
        return

    with open(SONGS_PATH, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"Target: {len(songs)} tracks")

    clap = ClapEncoder()
    embedder = LyricsEmbedder(clap)

    new_count = 0
    skipped_count = 0

    try:
        for i, s in enumerate(songs):
            if s.get("clap_embed") is not None and (isinstance(s["clap_embed"], list) and len(s["clap_embed"]) > 0):
                skipped_count += 1
                continue

            title = s.get("name") or s.get("title") 
            artists = s.get("artists", [])
            artist = artists if isinstance(artists, str) else (artists[0] if artists else "Unknown")
            
            if not title:
                continue

            time.sleep(0.15)
            
            print(f"[{i+1}/{len(songs)}] Processing: {title}...", end="\r")
            emb = embedder.embed_song(title, artist)

            if emb is not None:
                s["clap_embed"] = emb.tolist() if hasattr(emb, 'tolist') else emb
                new_count += 1
                print(f"[{i+1}/{len(songs)}] [SUCCESS] {title} - {artist}          ")
                
                if new_count % 5 == 0:
                    with open(SONGS_PATH, "w", encoding="utf-8") as f:
                        json.dump(songs, f, indent=2, ensure_ascii=False)
            else:
                print(f"[{i+1}/{len(songs)}] [FAILED] {title} - {artist}           ")

    except KeyboardInterrupt:
        print("\n\nManual Interruption. Cleaning up.")
    except Exception as e:
        print(f"\n\nFatal Error: {e}")
    finally:
        # 4. FINAL SYNC
        with open(SONGS_PATH, "w", encoding="utf-8") as f:
            json.dump(songs, f, indent=2, ensure_ascii=False)
        
        print(f"\n--- Process Complete ---")
        print(f"Cached: {skipped_count}")
        print(f"Added:  {new_count}")
        print(f"Total:  {len(songs)}")

if __name__ == "__main__":
    main()