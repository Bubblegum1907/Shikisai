import numpy as np

class UserProfile:
    def __init__(self, spotify_auth, store):
        """
        spotify_auth: SpotifyAuth instance
        store: SongStore (to map spotify ids to vectors)
        """
        self.spotify_auth = spotify_auth
        self.store = store

    def build_user_vector(self, access_token: str, limit=50):
        """
        Fetch user's top/saved tracks (via spotipy using spotify_auth) and average corresponding store vectors.
        If a spotify_id maps to multiple vector candidates, pick first match.
        """
        sp = self.spotify_auth.get_spotify_client(access_token)
        items = []
        try:
            top = sp.current_user_top_tracks(limit=limit).get("items", [])
            for t in top:
                items.append({"title": t.get("name"), "spotify_id": t.get("id"), "artists": [a.get("name") for a in t.get("artists", [])]})
        except Exception as e:
            print("top tracks fetch failed:", e)

        try:
            saved_resp = sp.current_user_saved_tracks(limit=limit)
            for s in saved_resp.get("items", []):
                t = s.get("track", {})
                items.append({"title": t.get("name"), "spotify_id": t.get("id"), "artists": [a.get("name") for a in t.get("artists", [])]})
        except Exception as e:
            print("saved tracks fetch failed:", e)

        # map spotify ids to store indices
        idxs = []
        id_to_idx = {}
        for i, m in enumerate(self.store.metadata):
            sid = m.get("spotify_id")
            if sid:
                id_to_idx[sid] = i

        for it in items:
            sid = it.get("spotify_id")
            if sid and sid in id_to_idx:
                idxs.append(id_to_idx[sid])
            else:
                # fallback: title substring match
                title = (it.get("title") or "").lower()
                for i, m in enumerate(self.store.metadata):
                    if title in (m.get("title") or "").lower():
                        idxs.append(i)
                        break

        if len(idxs) == 0:
            # return zero vector same shape as store vectors
            return np.zeros(self.store.vectors.shape[1], dtype="float32")

        vecs = self.store.vectors[idxs]
        mean = vecs.mean(axis=0)
        mean = mean / (np.linalg.norm(mean) + 1e-9)
        return mean.astype("float32")
