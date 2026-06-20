import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import time

# --- Setup Credentials ---
CLIENT_ID = "4ca8c05230df4097a63f9bc4a45667fd"
CLIENT_SECRET = "2bd7b20cab604ade80f56ace4cd588a8"

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

def fetch_accurate_metadata(track_ids):
    """
    Fetches official Spotify metrics and resolves the 'Genre Gap'.
    """
    results = []
    
    # Spotify allows requesting 50 tracks at a time for efficiency
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        
        # 1. Get basic track info (Artist ID, Album, Preview URL)
        tracks_info = sp.tracks(batch)['tracks']
        
        # 2. Get Audio Features (Energy, Valence, etc.)
        audio_features = sp.audio_features(batch)
        
        for j, track in enumerate(tracks_info):
            if not track or not audio_features[j]:
                continue
                
            feat = audio_features[j]
            artist_id = track['artists'][0]['id']
            
            # 3. Resolve Genres (Fetched from the Artist, not the Track)
            artist_info = sp.artist(artist_id)
            genres = artist_info.get('genres', [])
            
            metadata = {
                "id": track['id'],
                "name": track['name'],
                "artists": ", ".join([a['name'] for a in track['artists']]),
                "genres": genres,
                "energy": feat['energy'],
                "valence": feat['valence'],
                "danceability": feat['danceability'],
                "instrumentalness": feat['instrumentalness'],
                "acousticness": feat['acousticness'],
                "preview_url": track['preview_url']
            }
            results.append(metadata)
            print(f"Fetched: {track['name']} - Energy: {feat['energy']}")
            
        # Respect rate limits
        time.sleep(0.1) 
        
    return results

def save_clean_json(data, filename="song_metadata.json"):
    """Saves JSON without the escaped forward slashes (raw / instead of \/)"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Example: Arctic Monkeys - I Wanna Be Yours
    my_track_list = ["5XeFesFbtLpXzIVDNQP22n"] 
    
    final_data = fetch_accurate_metadata(my_track_list)
    save_clean_json(final_data)
    print(f"\n✨ Accurate metadata saved for {len(final_data)} tracks.")