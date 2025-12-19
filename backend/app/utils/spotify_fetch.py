# app/utils/spotify_fetch.py
from typing import List, Dict
from .spotify_auth import SpotifyAuth
import spotipy
import time

class SpotifyFetcher:
    """
    Helpers for fetching user's tracks/playlist tracks and simplifying them into small dicts:
    {"title": "...", "artists": ["a","b"], "album": "...", "artist_genres": ["g1","g2"], "spotify_id": "..."}
    """
    def __init__(self):
        self.auth = SpotifyAuth()

    def _safe_split_artists(self, artist_objs):
        return [a.get("name") for a in artist_objs] if artist_objs else []

    def fetch_tracks_from_user(self, access_token: str, fetch_playlists=True, fetch_saved=True, fetch_top=True, max_per_source=500) -> List[Dict]:
        sp = self.auth.get_spotify_client(access_token)
        seen = set()
        results = []

        if fetch_playlists:
            try:
                playlists = sp.current_user_playlists(limit=50)
                for p in playlists.get("items", []):
                    pid = p.get("id")
                    # iterate playlist items
                    tracks = sp.playlist_items(pid, limit=50)
                    while tracks:
                        for it in tracks.get("items", []):
                            t = it.get("track", {})
                            if not t: 
                                continue
                            sid = t.get("id")
                            if sid and sid not in seen:
                                seen.add(sid)
                                results.append(self._simplify_track(sp, t))
                                if len(results) >= max_per_source: break
                        if len(results) >= max_per_source: break
                        if tracks.get("next"):
                            tracks = sp.next(tracks)
                        else:
                            break
                    if len(results) >= max_per_source: break
            except Exception as e:
                print("playlist fetch failed:", e)

        if fetch_saved and len(results) < max_per_source:
            try:
                saved = sp.current_user_saved_tracks(limit=50)
                while saved:
                    for s in saved.get("items", []):
                        t = s.get("track", {})
                        sid = t.get("id")
                        if sid and sid not in seen:
                            seen.add(sid)
                            results.append(self._simplify_track(sp, t))
                            if len(results) >= max_per_source: break
                    if len(results) >= max_per_source: break
                    if saved.get("next"):
                        saved = sp.next(saved)
                    else:
                        break
            except Exception as e:
                print("saved fetch failed:", e)

        if fetch_top and len(results) < max_per_source:
            try:
                top = sp.current_user_top_tracks(limit=50)
                for t in top.get("items", []):
                    sid = t.get("id")
                    if sid and sid not in seen:
                        seen.add(sid)
                        results.append(self._simplify_track(sp, t))
                        if len(results) >= max_per_source: break
            except Exception as e:
                print("top tracks fetch failed:", e)

        return results

    def _simplify_track(self, sp_client: spotipy.Spotify, t: dict):
        # fetch artist genres
        artist_objs = t.get("artists", [])
        artist_genres = []
        for a in artist_objs:
            aid = a.get("id")
            try:
                info = sp_client.artist(aid)
                artist_genres.extend(info.get("genres", []))
            except Exception:
                pass
        return {
            "title": t.get("name"),
            "artists": [a.get("name") for a in artist_objs],
            "album": (t.get("album") or {}).get("name"),
            "artist_genres": list(set(artist_genres)),
            "spotify_id": t.get("id")
        }

    def enrich_genres(genres):
        if not genres:
            return []

        g = " ".join(genres).lower()
        tags = []

        if "jazz" in g: tags.append("smooth warm intimate")
        if "pop" in g: tags.append("bright melodic energetic")
        if "indie" in g: tags.append("nostalgic mellow emotional")
        if "rock" in g: tags.append("intense bold powerful")
        if "classical" in g: tags.append("elegant calm thoughtful")
        if "lofi" in g: tags.append("relaxed chilled soft sleepy")
        if "r&b" in g: tags.append("romantic soulful warm")

        return tags
    
    def get_user_taste_profile(self, access_token: str, limit=50):
        sp = self.auth.get_spotify_client(access_token)

        # 1) fetch user's top tracks
        top = sp.current_user_top_tracks(
            limit=min(limit, 50),
            time_range="medium_term"
        )
        items = top.get("items", [])
        if not items:
            return None

        track_ids = [t["id"] for t in items if t.get("id")]
        if not track_ids:
            return None

        # 2) fetch audio features
        feats = []

        for tid in track_ids:
            try:
                f = sp.audio_features([tid])[0]
                if f:
                    feats.append(f)
                time.sleep(0.05)  # gentle rate-limit
            except Exception as e:
                print("audio feature skipped:", tid)

        if not feats:
            return None

        # 3) average selected features
        def avg(key):
            vals = [f[key] for f in feats if f.get(key) is not None]
            return sum(vals) / len(vals) if vals else None

        return {
            "valence": avg("valence"),
            "energy": avg("energy"),
            "acousticness": avg("acousticness"),
            "danceability": avg("danceability"),
            "tempo": avg("tempo"),
        }
    
    def build_taste_from_tracks(self, tracks):
        if not tracks:
            return None

        genres = []
        years = []
        
        for t in tracks:
            genres.extend(t.get("artist_genres", []))
            album = t.get("album", "")
            # optional year extraction later if needed

        from collections import Counter
        genre_counts = Counter(genres)

        return {
            "top_genres": [g for g, _ in genre_counts.most_common(5)],
            "genre_counts": genre_counts,
            "prefers_soft": any(g in genres for g in ["indie", "acoustic", "lo-fi", "folk"]),
            "prefers_pop": any("pop" in g for g in genres),
        }



