"""
song_store.py

FAISS-backed store for song vectors.

Fixes:
- VAD dominance (d) was always 0.5 for every track — now read from
  track data where available, with 0.5 as a true fallback only.
- Vector dimension is enforced consistently throughout so FAISS never
  receives mismatched shapes.
- load_index() no longer raises on missing files — it returns gracefully
  so the app can start without a pre-built index.
- add_spotify_tracks() validates each vector before adding to prevent
  a single bad track from breaking the whole batch.
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Optional

TEXT_DIM = 512
AUDIO_DIM = 512
VAD_DIM = 3
FINAL_DIM = TEXT_DIM + AUDIO_DIM + VAD_DIM  # 1027


class SongStore:
    def __init__(self, clap, data_dir: str = "data"):
        self.clap = clap
        self.dim = FINAL_DIM

        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict] = []
        self.index: Optional[faiss.Index] = None
        self.seen_ids: set = set()

        os.makedirs(data_dir, exist_ok=True)
        self.index_path = os.path.join(data_dir, "faiss.index")
        self.vectors_path = os.path.join(data_dir, "song_vectors.npy")
        self.meta_path = os.path.join(data_dir, "song_metadata.json")

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _clean_text_embedding(self, raw) -> Optional[np.ndarray]:
        """Force a text embedding to exactly TEXT_DIM (512) dims."""
        if raw is None:
            return None

        if isinstance(raw, dict):
            arr = raw.get("embedding") or raw.get("vector") or raw.get("vec")
        else:
            arr = raw

        try:
            arr = np.array(arr, dtype=np.float32).flatten()
        except Exception as e:
            print(f"[SongStore] Could not convert embedding to array: {e}")
            return None

        if arr.size == 0:
            return None

        if arr.size >= TEXT_DIM:
            return arr[:TEXT_DIM]
        return np.pad(arr, (0, TEXT_DIM - arr.size))

    def _make_song_vector(
        self,
        text_output,
        v: float = 0.5,
        a: float = 0.5,
        d: float = 0.5,
    ) -> Optional[np.ndarray]:
        """
        Builds the full FINAL_DIM (1027) vector.

        Layout:
          [0:512]    — text (CLAP) embedding
          [512:1024] — audio embedding (zeros until audio features available)
          [1024:1027] — VAD: valence, arousal, dominance

        All three VAD values are now real parameters, not hardcoded.
        """
        text_emb = self._clean_text_embedding(text_output)
        if text_emb is None:
            return None

        audio_emb = np.zeros(AUDIO_DIM, dtype=np.float32)

        # Clamp VAD values to [0, 1]
        vad = np.array(
            [np.clip(v, 0.0, 1.0), np.clip(a, 0.0, 1.0), np.clip(d, 0.0, 1.0)],
            dtype=np.float32,
        )

        vec = np.concatenate([text_emb, audio_emb, vad])
        norm = np.linalg.norm(vec)
        if norm < 1e-9:
            return None
        return (vec / norm).astype(np.float32)

    def _build_faiss(self):
        """Rebuilds the in-memory FAISS index from self.vectors."""
        if self.vectors is None or len(self.vectors) == 0:
            return
        index = faiss.IndexFlatIP(self.dim)
        index.add(self.vectors)
        self.index = index
        faiss.write_index(index, self.index_path)
        print(f"[SongStore] FAISS index updated: {len(self.vectors)} tracks.")

    def _persist(self):
        """Saves vectors and metadata to disk."""
        if self.vectors is not None:
            np.save(self.vectors_path, self.vectors)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def add_spotify_tracks(
        self,
        tracks: List[Dict],
        color_hex: Optional[str] = None,
    ) -> int:
        """
        Encodes and indexes a list of Spotify track dicts.

        Each track dict should contain at minimum:
          spotify_id, title/name, artists, valence, energy

        Returns the number of new tracks successfully added.
        """
        if not isinstance(tracks, list) or not tracks:
            return 0

        from app.utils.color_to_text import color_to_text_prompt

        # Fallback prompt + VAD used when a track has no native audio features
        fallback_prompt = ""
        fallback_v, fallback_a = 0.5, 0.5
        if color_hex:
            try:
                fallback_prompt, (fallback_v, fallback_a) = color_to_text_prompt(color_hex)
            except Exception as e:
                print(f"[SongStore] color_to_text_prompt failed: {e}")

        new_vecs: List[np.ndarray] = []
        new_meta: List[Dict] = []

        for t in tracks:
            spotify_id = t.get("spotify_id") or t.get("id")
            if not spotify_id or spotify_id in self.seen_ids:
                continue

            # Normalise artist list
            artists_raw = t.get("artists") or []
            if isinstance(artists_raw, str):
                artists = [artists_raw]
            else:
                artists = [
                    a.get("name") if isinstance(a, dict) else str(a)
                    for a in artists_raw
                ]

            title = t.get("title") or t.get("name") or "Unknown"
            genres: List[str] = t.get("artist_genres") or t.get("genres") or []

            # FIX: read all three VAD dimensions from the track
            track_v = float(t.get("valence", fallback_v))
            track_a = float(t.get("energy", fallback_a))
            # Dominance: use speechiness as a proxy (more speech → more dominant)
            # Falls back to 0.5 if unavailable
            track_d = float(t.get("dominance", t.get("speechiness", 0.5)))

            text_desc = (
                f"Song '{title}' by {', '.join(artists)}. "
                f"Genres: {', '.join(genres)}. "
                f"Context: {fallback_prompt}"
            )

            try:
                text_out = self.clap.encode_text(text_desc)
                vec = self._make_song_vector(text_out, v=track_v, a=track_a, d=track_d)

                if vec is None:
                    print(f"[SongStore] Skipping {spotify_id} — vector is None.")
                    continue

                if vec.shape[0] != self.dim:
                    print(
                        f"[SongStore] Skipping {spotify_id} — "
                        f"vector dim {vec.shape[0]} != {self.dim}."
                    )
                    continue

                new_vecs.append(vec)
                new_meta.append({
                    "spotify_id": spotify_id,
                    "title": title,
                    "artists": artists,
                    "genres": genres,
                    "valence": track_v,
                    "energy": track_a,
                    "vad_score": [track_v, track_a, track_d],
                    "speechiness": float(t.get("speechiness", 0.0)),
                    "instrumentalness": float(t.get("instrumentalness", 0.0)),
                    "album": t.get("album", ""),
                    "image_url": t.get("image_url", ""),
                    "preview_url": t.get("preview_url", None),
                    "source": "spotify",
                })
                self.seen_ids.add(spotify_id)

            except Exception as e:
                print(f"[SongStore] Error encoding {spotify_id} ('{title}'): {e}")
                continue

        if not new_vecs:
            return 0

        new_vecs_np = np.stack(new_vecs).astype(np.float32)

        if self.vectors is None:
            self.vectors = new_vecs_np
            self.metadata = new_meta
        else:
            self.vectors = np.vstack([self.vectors, new_vecs_np])
            self.metadata.extend(new_meta)

        self._persist()
        self._build_faiss()

        print(f"[SongStore] Added {len(new_vecs)} new tracks. Total: {len(self.metadata)}.")
        return len(new_vecs)

    def load_index(self):
        """
        Loads persisted vectors and metadata from disk.
        Returns silently if files don't exist — no exception raised.
        """
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.seen_ids = {
                    m["spotify_id"]
                    for m in self.metadata
                    if "spotify_id" in m
                }
                print(f"[SongStore] Loaded {len(self.metadata)} metadata entries.")
            except Exception as e:
                print(f"[SongStore] Could not load metadata: {e}")
                self.metadata = []

        if os.path.exists(self.vectors_path):
            try:
                self.vectors = np.load(self.vectors_path).astype(np.float32)
                print(f"[SongStore] Loaded vectors: {self.vectors.shape}")
                self._build_faiss()
            except Exception as e:
                print(f"[SongStore] Could not load vectors: {e}")
                self.vectors = None

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict]:
        """
        Returns the top-k most similar tracks by inner product.
        Returns empty list if the index is not built yet.
        """
        if self.index is None:
            return []

        q = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        norm = np.linalg.norm(q)
        if norm > 1e-9:
            q = q / norm

        D, I = self.index.search(q, k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if 0 <= idx < len(self.metadata):
                meta = self.metadata[idx].copy()
                meta["score"] = float(score)
                results.append(meta)
        return results

    @property
    def size(self) -> int:
        """Number of tracks currently in the store."""
        return len(self.metadata)