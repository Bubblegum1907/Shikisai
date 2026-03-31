import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv

# 1. Setup paths
backend_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=backend_root / ".env")

# 2. Authentication (This handles the token for you!)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:9000",
    scope="user-library-read playlist-read-private playlist-read-collaborative"
))

def run_recovery():
    print("🌐 Opening browser... Please log in and authorize.")
    user = sp.current_user()
    print(f"✅ Connected to: {user['display_name']}")

    all_tracks = []
    seen_ids = set()

    # --- PART A: LIKED SONGS ---
    print("📥 Fetching Liked Songs...")
    results = sp.current_user_saved_tracks(limit=50)
    while results:
        for item in results['items']:
            t = item['track']
            if t['id'] not in seen_ids:
                all_tracks.append({
                    "id": t['id'], "name": t['name'], 
                    "artists": ", ".join([a['name'] for a in t['artists'] if a.get('name')]),
                    "album": t['album']['name'], "source": "Liked Songs"
                })
                seen_ids.add(t['id'])
        results = sp.next(results) if results['next'] else None

    # --- PART B: PLAYLISTS (YOURS + FOLLOWED) ---
    print("📥 Fetching all Playlists (yours + followed)...")
    playlists = sp.current_user_playlists()
    while playlists:
        for pl in playlists['items']:
            print(f"  > Processing: {pl['name']} ({pl['tracks']['total']} tracks)")
            tracks = sp.playlist_tracks(pl['id'])
            while tracks:
                for item in tracks['items']:
                    if item['track'] and item['track']['id'] not in seen_ids:
                        t = item['track']
                        all_tracks.append({
                            "id": t['id'], "name": t['name'], 
                            "artists": ", ".join([a['name'] for a in t['artists'] if a.get('name')]),
                            "album": t['album']['name'], "source": pl['name']
                        })
                        seen_ids.add(t['id'])
                tracks = sp.next(tracks) if tracks['next'] else None
        playlists = sp.next(playlists) if playlists['next'] else None

    # --- SAVE ---
    df = pd.DataFrame(all_tracks)
    csv_path = backend_root / "data" / "my_tracks_with_clap.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✨ DONE! {len(df)} unique tracks recovered.")
    print(f"📁 Saved to: {csv_path}")

if __name__ == "__main__":
    run_recovery()