# app/utils/spotify_fetch.py
from typing import List, Dict
from spotipy.exceptions import SpotifyException
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

    def _with_refresh(self, access_token, refresh_token, fn):
        sp = self.auth.get_spotify_client(access_token)
        try:
            return fn(sp)
        except SpotifyException as e:
            if e.http_status == 401:
                print("🔁 Refreshing Spotify token")
                new_token = self.auth.refresh_access_token(refresh_token)
                sp = self.auth.get_spotify_client(new_token)
                return fn(sp)
            else:
                raise

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
    
    def get_user_taste_profile(self, access_token: str, refresh_token: str, limit=50):
        """
        Builds a lightweight taste profile from the user's top tracks.
        Automatically refreshes Spotify token if it expires.
        """

        # Fetch user's top tracks (with refresh support)
        try:
            top = self._with_refresh(
                access_token,
                refresh_token,
                lambda sp: sp.current_user_top_tracks(
                    limit=min(limit, 50),
                    time_range="medium_term"
                )
            )
        except Exception as e:
            print("top tracks fetch failed:", e)
            return None

        items = top.get("items", [])
        if not items:
            return None

        track_ids = [t.get("id") for t in items if t.get("id")]
        if not track_ids:
            return None

        # Fetch audio features
        feats = []

        # Spotify allows max 100 IDs per request
        def chunks(lst, n=50):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        for chunk in chunks(track_ids, 50):
            try:
                chunk_feats = self._with_refresh(
                    access_token,
                    refresh_token,
                    lambda sp: sp.audio_features(tracks=chunk)
                )
                feats.extend([f for f in chunk_feats if f])
            except Exception as e:
                print("audio features chunk skipped:", e)

        if not feats:
            print("No audio features available — falling back to non-audio taste")
            return None


        # Average selected features
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



