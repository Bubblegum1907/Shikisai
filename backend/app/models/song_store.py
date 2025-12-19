# app/models/song_store.py
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Optional

from app.utils.color_to_text import color_to_emotion

# -------------------------
# Fixed dimensions
# -------------------------
TEXT_DIM = 512
AUDIO_DIM = 512
VAD_DIM = 3
FINAL_DIM = TEXT_DIM + AUDIO_DIM + VAD_DIM  # 1027

# -------------------------
# SongStore
# -------------------------
class SongStore:
    """
    FAISS-backed store for 1027-d song vectors (512 text + 512 audio + 3 VAD).
    - add_spotify_tracks(tracks): accepts simplified track dicts from spotify_fetcher
    - load_index(), _build_faiss(), search(q, k)
    - build_from_local(audio_dir): optional helper to encode local audio files (fallback)
    """

    def __init__(self, clap, data_dir: str = "data"):
        self.clap = clap
        self.dim = FINAL_DIM

        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict] = []
        self.index: Optional[faiss.Index] = None
        self.seen_ids = set()

        os.makedirs(data_dir, exist_ok=True)
        self.index_path = os.path.join(data_dir, "faiss.index")
        self.vectors_path = os.path.join(data_dir, "song_vectors.npy")
        self.meta_path = os.path.join(data_dir, "song_metadata.json")

    # -------------------------
    # Helpers: clean text embedding to 512 dims
    # -------------------------
    def _extract_embedding_from_obj(self, obj):
        """
        Accept different CLAP outputs:
         - dict with 'embedding' or 'vector' or 'vec'
         - list/ndarray
        Return numpy 1D array or None.
        """
        if obj is None:
            return None
        if isinstance(obj, dict):
            emb = obj.get("embedding") or obj.get("vector") or obj.get("vec")
            if emb is None:
                return None
            arr = np.array(emb, dtype=np.float32).flatten()
            return arr
        try:
            arr = np.array(obj, dtype=np.float32).flatten()
            return arr
        except Exception:
            return None

    def _clean_text_embedding(self, raw):
        """
        Force text embedding to exactly TEXT_DIM (512).
        Truncate if larger, pad with zeros if smaller.
        """
        arr = self._extract_embedding_from_obj(raw)
        if arr is None:
            return None
        if arr.size >= TEXT_DIM:
            return arr[:TEXT_DIM].astype(np.float32)
        else:
            pad = np.zeros(TEXT_DIM - arr.size, dtype=np.float32)
            return np.concatenate([arr.astype(np.float32), pad])

    # -------------------------
    # Build full 1027-d vector
    # -------------------------
    def _make_song_vector(self, text_output) -> Optional[np.ndarray]:
        """
        Convert CLAP text output (whatever it is) into a strict 1027-d normalized vector.
        Returns None if text_output cannot be interpreted.
        """
        text_emb = self._clean_text_embedding(text_output)
        if text_emb is None:
            return None

        audio_emb = np.zeros(AUDIO_DIM, dtype=np.float32)  # placeholder
        vad = np.zeros(VAD_DIM, dtype=np.float32)  # placeholder

        vec = np.concatenate([text_emb, audio_emb, vad]).astype(np.float32)
        norm = np.linalg.norm(vec) + 1e-9
        return vec / norm

    # -------------------------
    # Add Spotify tracks
    # -------------------------
    def add_spotify_tracks(self, tracks: List[Dict], color_hex: Optional[str] = None) -> int:
        """
        Accepts a list of simplified track dicts (from spotify_fetcher).
        Returns number of tracks added.
        Robust: logs skipped tracks and reasons.
        """
        if not isinstance(tracks, list):
            print("add_spotify_tracks: expected list, got", type(tracks))
            return 0

        new_vecs = []
        new_meta = []
        skipped = 0
        encoded_failures = 0

        for i, t in enumerate(tracks):
            # Robust spotify_id extraction (playlist items, direct items, varied shapes)
            spotify_id = (
                t.get("spotify_id")
                or t.get("id")
                or (t.get("track") or {}).get("id")
                or (t.get("track") or {}).get("spotify_id")
            )
            if not spotify_id:
                print(f"[SongStore] SKIP#{i}: missing spotify_id -> item={t}")
                skipped += 1
                continue
            if spotify_id in self.seen_ids:
                # duplicate
                # print(f"[SongStore] SKIP#{i}: already seen {spotify_id}")
                continue

            # Normalize artists list: accept both list of names or list of objects
            artists_raw = t.get("artists") or []
            if artists_raw and isinstance(artists_raw[0], dict):
                artists = [a.get("name") for a in artists_raw if a.get("name")]
            else:
                artists = [str(a) for a in artists_raw] if artists_raw else []

            title = t.get("title") or t.get("name") or (t.get("track") or {}).get("name") or ""
            genres = t.get("artist_genres") or t.get("genres") or []

            # Mood injection (optional)
            if color_hex:
                mood = color_to_emotion(color_hex)
                mood_line = f" This song relates to emotions like {mood}."
            else:
                mood_line = ""

            text_desc = f"Song '{title}' by {', '.join(artists)}. Genres: {', '.join(genres)}.{mood_line}"

            # Encode text with CLAP
            try:
                text_out = self.clap.encode_text(text_desc)
            except Exception as e:
                print(f"[SongStore] CLAP encode EXCEPTION for {spotify_id}: {e}")
                encoded_failures += 1
                continue

            vec = self._make_song_vector(text_out)
            if vec is None:
                print(f"[SongStore] SKIP#{i}: failed to parse embedding for {spotify_id} (raw size unknown)")
                encoded_failures += 1
                continue

            new_vecs.append(vec)
            new_meta.append({
                "spotify_id": spotify_id,
                "title": title,
                "artists": artists,
                "genres": genres,
                "source": "spotify",
            })
            self.seen_ids.add(spotify_id)

        if not new_vecs:
            print(f"[SongStore] No vectors added. skipped={skipped}, encode_failures={encoded_failures}")
            return 0

        new_vecs = np.stack(new_vecs).astype(np.float32)

        if self.vectors is None:
            self.vectors = new_vecs
            self.metadata = new_meta
        else:
            # verify dims and pad/trim if necessary (shouldn't be needed)
            if self.vectors.shape[1] != new_vecs.shape[1]:
                # try to realign by trimming/padding existing or new vectors
                expected = self.dim
                existing_d = self.vectors.shape[1]
                new_d = new_vecs.shape[1]
                if existing_d != expected:
                    # attempt to pad/truncate existing
                    if existing_d > expected:
                        self.vectors = self.vectors[:, :expected]
                    else:
                        pad = np.zeros((self.vectors.shape[0], expected - existing_d), dtype=np.float32)
                        self.vectors = np.hstack([self.vectors, pad])
                if new_d != expected:
                    if new_d > expected:
                        new_vecs = new_vecs[:, :expected]
                    else:
                        pad = np.zeros((new_vecs.shape[0], expected - new_d), dtype=np.float32)
                        new_vecs = np.hstack([new_vecs, pad])

            self.vectors = np.vstack([self.vectors, new_vecs])
            self.metadata.extend(new_meta)

        # persist
        np.save(self.vectors_path, self.vectors)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        # rebuild faiss
        self._build_faiss()

        added = len(new_vecs)
        print(f"[SongStore] Added {added} new vectors (skipped={skipped}, encode_failures={encoded_failures})")
        return added

    # -------------------------
    # Optional: build from local audio files (simple placeholder)
    # -------------------------
    def build_from_local(self, audio_dir: str):
        """
        Simple helper that looks for audio files and encodes filenames + metadata to text vectors.
        This is a lightweight fallback (not high quality audio encoding).
        """
        if not os.path.exists(audio_dir):
            raise FileNotFoundError(f"Audio dir not found: {audio_dir}")

        files = []
        for root, _, filenames in os.walk(audio_dir):
            for fn in filenames:
                if fn.lower().endswith((".mp3", ".wav", ".flac", ".m4a")):
                    files.append(os.path.join(root, fn))

        tracks = []
        for p in files:
            title = os.path.splitext(os.path.basename(p))[0]
            tracks.append({
                "spotify_id": f"local::{title}",
                "title": title,
                "artists": ["local"],
                "artist_genres": ["local"],
            })

        return self.add_spotify_tracks(tracks)

    # -------------------------
    # FAISS build / load / search
    # -------------------------
    def _build_faiss(self):
        if self.vectors is None or self.vectors.shape[0] == 0:
            raise RuntimeError("No vectors to build FAISS index.")

        if self.vectors.shape[1] != self.dim:
            raise ValueError(f"Vector dim mismatch: {self.vectors.shape[1]} vs expected {self.dim}")

        # ensure normalized
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-9
        self.vectors = self.vectors / norms

        index = faiss.IndexFlatIP(self.dim)
        index.add(self.vectors)
        self.index = index

        faiss.write_index(index, self.index_path)
        print(f"[SongStore] FAISS index built with {self.vectors.shape[0]} vectors (dim={self.dim})")

    def load_index(self):
        # load metadata if exists
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            for m in self.metadata:
                sid = m.get("spotify_id") or m.get("id")
                if sid:
                    self.seen_ids.add(sid)

        # load vectors if exists
        if os.path.exists(self.vectors_path):
            self.vectors = np.load(self.vectors_path).astype(np.float32)

        # load index or rebuild
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                print(f"[SongStore] Loaded FAISS index from {self.index_path}")
            except Exception as e:
                print("[SongStore] Failed to read index, rebuilding:", e)
                self._build_faiss()
        else:
            if self.vectors is not None and self.vectors.shape[0] > 0:
                self._build_faiss()
            else:
                self.index = None

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict]:
        if self.index is None:
            raise RuntimeError("Index not loaded.")

        q = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError(f"Query vector dimension {q.shape[1]} != expected {self.dim}")

        q = q / (np.linalg.norm(q) + 1e-9)

        D, I = self.index.search(q, k)
        results = []
        for score, idx in zip(D[0], I[0]):
            meta = self.metadata[idx].copy()
            meta["score"] = float(score)
            meta["idx"] = int(idx)
            results.append(meta)
        return results
