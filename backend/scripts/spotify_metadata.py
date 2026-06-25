import os
import json
import time
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend root
BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BACKEND_ROOT / ".env")

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be set in your .env file. "
        "Never hardcode credentials in source files."
    )

auth_manager = SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)
sp = spotipy.Spotify(auth_manager=auth_manager)


def fetch_accurate_metadata(track_ids: list) -> list:
    """
    Fetches official Spotify metrics and resolves the 'Genre Gap'.
    Processes in batches of 50 (Spotify API limit).
    """
    results = []

    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i + 50]

        # 1. Basic track info (artist ID, album, preview URL)
        tracks_info = sp.tracks(batch).get("tracks", [])

        # 2. Audio features (energy, valence, etc.)
        audio_features = sp.audio_features(batch)

        for j, track in enumerate(tracks_info):
            if not track or not audio_features[j]:
                continue

            feat = audio_features[j]
            artist_id = track["artists"][0]["id"]

            # 3. Genres come from the artist, not the track
            try:
                artist_info = sp.artist(artist_id)
                genres = artist_info.get("genres", [])
            except Exception as e:
                print(f"  Warning: Could not fetch genres for artist {artist_id}: {e}")
                genres = []

            metadata = {
                "id": track["id"],
                "name": track["name"],
                "artists": ", ".join(a["name"] for a in track["artists"]),
                "genres": genres,
                "energy": feat["energy"],
                "valence": feat["valence"],
                "danceability": feat["danceability"],
                "instrumentalness": feat["instrumentalness"],
                "acousticness": feat["acousticness"],
                "preview_url": track.get("preview_url"),
            }
            results.append(metadata)
            print(f"  Fetched: {track['name']} — Energy: {feat['energy']:.2f}")

        # Respect Spotify rate limits
        time.sleep(0.1)

    return results


def save_clean_json(data: list, filepath: Path) -> None:
    """Saves JSON without escaped forward slashes."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} tracks to {filepath}")


if __name__ == "__main__":
    # Replace with your actual track IDs
    my_track_list = ["5XeFesFbtLpXzIVDNQP22n"]

    print(f"Fetching metadata for {len(my_track_list)} tracks...")
    final_data = fetch_accurate_metadata(my_track_list)

    out_path = BACKEND_ROOT / "data" / "song_metadata.json"
    save_clean_json(final_data, out_path)
    print(f"\nDone. Accurate metadata saved for {len(final_data)} tracks.")