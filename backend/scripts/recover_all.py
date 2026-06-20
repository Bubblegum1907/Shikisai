import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
from spotipy.exceptions import SpotifyException

# 1. Setup paths
backend_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=backend_root / ".env")
csv_path = backend_root / "data" / "my_tracks_with_clap.csv"

# 2. Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:9000",
    scope="user-library-read playlist-read-private playlist-read-collaborative"
))

def fetch_tracks_paginated(sp, method, **kwargs):
    """Safely yields tracks from any Spotify pagination object."""
    try:
        results = method(**kwargs)
        while results:
            for item in results.get('items', []):
                track = item.get('track')
                if track and track.get('id'):
                    yield track
            
            if results.get('next'):
                results = sp.next(results)
            else:
                break
    except SpotifyException as e:
        print(f"API Pagination Error: {e}")

def run_recovery():
    if csv_path.exists():
        print(f"Loading existing library from {csv_path.name}...")
        existing_df = pd.read_csv(csv_path)
        seen_ids = set(existing_df['id'].unique())
        all_tracks = existing_df.to_dict('records')
    else:
        print("No existing CSV found. Creating a new one.")
        existing_df = pd.DataFrame()
        seen_ids = set()
        all_tracks = []

    def process_track(t):
        if not t or t.get('id') in seen_ids:
            return
        
        artist_list = [a['name'] for a in t.get('artists', []) if a.get('name')]
        artists_str = ", ".join(artist_list) if artist_list else "Unknown Artist"

        all_tracks.append({
            "id": t['id'],
            "name": t.get('name', 'Unknown Track'),
            "artists": artists_str,
            "genres": "[]", 
            "clap_embed": "[]", 
            "valence": 0.5,    
            "energy": 0.5
        })
        seen_ids.add(t['id'])

    print("Syncing with Spotify...")
    for track in fetch_tracks_paginated(sp, sp.current_user_saved_tracks, limit=50):
        process_track(track)

    if not all_tracks:
        print("No new tracks to add.")
        return

    df = pd.DataFrame(all_tracks)
    
    columns = ["id", "name", "artists", "genres", "clap_embed", "valence", "energy"]
    df = df[columns]

    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"\nDone. {len(df)} total tracks now in {csv_path.name}.")

if __name__ == "__main__":
    run_recovery()