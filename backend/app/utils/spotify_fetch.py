from typing import List, Dict, Optional
from spotipy.exceptions import SpotifyException
from .spotify_auth import SpotifyAuth
import spotipy
from collections import Counter

class SpotifyFetcher:
    """
    Optimized helpers for fetching user's tracks. 
    Handles large libraries using batching and multiple sources.
    """
    def __init__(self):
        self.auth = SpotifyAuth()
        self.artist_cache = {}

    def _get_sp_client(self, access_token: str):
        """Helper to get a client and verify it immediately."""
        try:
            return spotipy.Spotify(auth=access_token)
        except Exception as e:
            print(f"❌ Failed to initialize Spotify client: {e}")
            return None

    def _get_batch_genres(self, sp, artist_ids: List[str]):
        """Fetches genres for up to 50 artists in a single call."""
        new_ids = [aid for aid in artist_ids if aid and aid not in self.artist_cache]
        if not new_ids: return

        for i in range(0, len(new_ids), 50):
            chunk = new_ids[i:i + 50]
            try:
                artists_data = sp.artists(chunk)
                for a_data in artists_data.get('artists', []):
                    if a_data:
                        self.artist_cache[a_data['id']] = a_data.get('genres', [])
            except Exception as e:
                print(f"⚠️ Batch artist fetch failed: {e}")

    def fetch_tracks_from_user(self, 
                                access_token: str, 
                                fetch_playlists: bool = True, 
                                fetch_saved: bool = True, 
                                fetch_top: bool = True, 
                                max_per_source: int = 2000, # Increased limit
                                **kwargs) -> List[Dict]:
            sp = self._get_sp_client(access_token)
            if not sp: return []

            seen = set()
            raw_tracks = []

            try:
                if fetch_saved:
                    print("[SpotifyFetcher] Deep-fetching ALL saved tracks...")
                    results = sp.current_user_saved_tracks(limit=50)
                    while results:
                        items = [it.get("track") for it in results.get("items", []) if it.get("track")]
                        raw_tracks.extend(items)
                        if not results.get("next") or len(raw_tracks) >= max_per_source: break
                        results = sp.next(results)
                        print(f"  > Progress: {len(raw_tracks)} tracks...")

                if fetch_top:
                    print("[SpotifyFetcher] Fetching top tracks (Short/Med/Long term)...")
                    for trange in ["short_term", "medium_term", "long_term"]:
                        top = sp.current_user_top_tracks(limit=50, time_range=trange)
                        if top:
                            raw_tracks.extend([t for t in top.get("items", []) if t])

                if fetch_playlists:
                    print("[SpotifyFetcher] Scanning up to 50 playlists...")
                    playlists = sp.current_user_playlists(limit=50) 
                    for pl in playlists.get('items', []):
                        print(f"  > Scoping playlist: {pl['name']}")
                        pl_tracks = sp.playlist_tracks(pl['id'], limit=100)
                        while pl_tracks:
                            items = [it.get("track") for it in pl_tracks.get("items", []) if it.get("track")]
                            raw_tracks.extend(items)
                            if not pl_tracks.get("next") or len(raw_tracks) >= (max_per_source * 2): break
                            pl_tracks = sp.next(pl_tracks)

            except SpotifyException as e:
                print(f"❌ Spotify API Error: {e}")
                return []

            all_artist_ids = set()
            unique_tracks = []
            for t in raw_tracks:
                sid = t.get("id")
                if sid and sid not in seen:
                    seen.add(sid)
                    unique_tracks.append(t)
                    for a in t.get("artists", []):
                        if a.get("id"): all_artist_ids.add(a.get("id"))

            self._get_batch_genres(sp, list(all_artist_ids))

            results = []
            for t in unique_tracks:
                a_ids = [a.get("id") for a in t.get("artists", [])]
                genres = []
                for aid in a_ids:
                    genres.extend(self.artist_cache.get(aid, []))
                
                results.append({
                    "title": t.get("name"),
                    "artists": [a.get("name") for a in t.get("artists", [])],
                    "album": (t.get("album") or {}).get("name"),
                    "artist_genres": list(set(genres)),
                    "spotify_id": t.get("id")
                })
            
            return results

    def get_user_taste_profile(self, access_token: str, refresh_token: str):
        """Builds profile from audio features."""
        sp = self._get_sp_client(access_token)
        if not sp: return None

        try:
            top = sp.current_user_top_tracks(limit=50, time_range="medium_term")
            items = top.get("items", []) if top else []
            if not items: return None

            track_ids = [t.get("id") for t in items if t.get("id")]
            feats_data = sp.audio_features(tracks=track_ids)
            feats = [f for f in feats_data if f]

            def avg(key):
                vals = [f[key] for f in feats if f.get(key) is not None]
                return sum(vals) / len(vals) if vals else 0.5

            return {
                "valence": avg("valence"),
                "energy": avg("energy"),
                "acousticness": avg("acousticness"),
                "danceability": avg("danceability"),
                "tempo": avg("tempo"),
            }
        except Exception as e:
            print(f"Taste profile failed: {e}")
            return None

    def build_taste_from_tracks(self, tracks: List[Dict]):
        """Builds a simple genre-based profile from a list of track dicts."""
        if not tracks: return None
        
        genres = []
        for t in tracks:
            genres.extend(t.get("artist_genres", []))

        genre_counts = Counter(genres)
        return {
            "top_genres": [g for g, _ in genre_counts.most_common(5)],
            "genre_counts": dict(genre_counts),
            "prefers_soft": any(g in genres for g in ["indie", "acoustic", "lo-fi", "folk"]),
            "prefers_pop": any("pop" in g for g in genres),
        }