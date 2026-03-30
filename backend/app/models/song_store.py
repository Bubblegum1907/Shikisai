# app/models/song_store.py
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Optional

# Fixed dimensions based on your architecture
TEXT_DIM = 512
AUDIO_DIM = 512
VAD_DIM = 3
FINAL_DIM = TEXT_DIM + AUDIO_DIM + VAD_DIM  # 1027

class SongStore:
    """
    FAISS-backed store for 1027-d song vectors.
    Uses real VAD values to prevent recommendation overlap.
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

    def _clean_text_embedding(self, raw):
        """Force text embedding to exactly 512 dims."""
        if raw is None: return None
        
        # Extract array from potential dict wrapper
        if isinstance(raw, dict):
            arr = raw.get("embedding") or raw.get("vector") or raw.get("vec")
        else:
            arr = raw

        arr = np.array(arr, dtype=np.float32).flatten()
        
        if arr.size >= TEXT_DIM:
            return arr[:TEXT_DIM]
        else:
            return np.pad(arr, (0, TEXT_DIM - arr.size))

    def _make_song_vector(self, text_output, v=0.5, a=0.5, d=0.5) -> Optional[np.ndarray]:
        """
        Builds the full 1027-d vector using REAL VAD values.
        v: Valence, a: Arousal, d: Dominance (defaults to 0.5)
        """
        text_emb = self._clean_text_embedding(text_output)
        if text_emb is None:
            return None

        # Placeholder for audio features (512-d)
        audio_emb = np.zeros(AUDIO_DIM, dtype=np.float32)
        
        # Real Affective features (3-d)
        vad = np.array([v, a, d], dtype=np.float32)

        vec = np.concatenate([text_emb, audio_emb, vad]).astype(np.float32)
        
        # L2 Normalization is critical for FAISS IndexFlatIP
        norm = np.linalg.norm(vec) + 1e-9
        return vec / norm

    def add_spotify_tracks(self, tracks: List[Dict], color_hex: Optional[str] = None) -> int:
        """
        Adds tracks and uses color_to_text_prompt to inject emotional coordinates.
        """
        if not isinstance(tracks, list): return 0

        from app.utils.color_to_text import color_to_text_prompt
        
        new_vecs = []
        new_meta = []
        
        # Get the global emotional context for this color batch
        batch_prompt = ""
        v, a = 0.5, 0.5
        if color_hex:
            batch_prompt, (v, a) = color_to_text_prompt(color_hex)

        for t in tracks:
            spotify_id = t.get("spotify_id") or t.get("id")
            if not spotify_id or spotify_id in self.seen_ids:
                continue

            title = t.get("title") or t.get("name") or "Unknown"
            artists_raw = t.get("artists") or []
            artists = [a.get("name") if isinstance(a, dict) else str(a) for a in artists_raw]
            genres = t.get("artist_genres") or t.get("genres") or []

            # Hybrid description: metadata + emotional prompt
            text_desc = f"Song '{title}' by {', '.join(artists)}. Genres: {', '.join(genres)}. Context: {batch_prompt}"

            try:
                # 1. Encode with CLAP (Semantic)
                text_out = self.clap.encode_text(text_desc)
                
                # 2. Add VAD Coordinates (Affective)
                vec = self._make_song_vector(text_out, v=v, a=a)
                
                if vec is not None:
                    new_vecs.append(vec)
                    new_meta.append({
                        "spotify_id": spotify_id,
                        "title": title,
                        "artists": artists,
                        "genres": genres,
                        "vad_score": [float(v), float(a), 0.5],
                        "source": "spotify",
                    })
                    self.seen_ids.add(spotify_id)
            except Exception as e:
                print(f"[SongStore] Error encoding {spotify_id}: {e}")
                continue

        if not new_vecs: return 0

        # Update local storage
        new_vecs_np = np.stack(new_vecs).astype(np.float32)
        if self.vectors is None:
            self.vectors = new_vecs_np
            self.metadata = new_meta
        else:
            self.vectors = np.vstack([self.vectors, new_vecs_np])
            self.metadata.extend(new_meta)

        # Persist to disk
        np.save(self.vectors_path, self.vectors)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        # Rebuild the searchable index
        self._build_faiss()
        return len(new_vecs)

    def _build_faiss(self):
        if self.vectors is None or len(self.vectors) == 0: return
        
        # FAISS IndexFlatIP (Inner Product) works best with normalized vectors
        index = faiss.IndexFlatIP(self.dim)
        index.add(self.vectors)
        self.index = index
        faiss.write_index(index, self.index_path)
        print(f"[SongStore] Index updated: {len(self.vectors)} songs.")

    def load_index(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
                self.seen_ids = {m["spotify_id"] for m in self.metadata if "spotify_id" in m}

        if os.path.exists(self.vectors_path):
            self.vectors = np.load(self.vectors_path).astype(np.float32)
            self._build_faiss()

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict]:
        if self.index is None: return []
        
        q = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        q = q / (np.linalg.norm(q) + 1e-9) # Normalize query

        D, I = self.index.search(q, k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(self.metadata):
                meta = self.metadata[idx].copy()
                meta["score"] = float(score)
                results.append(meta)
        return results