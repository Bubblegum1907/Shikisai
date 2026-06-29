"""
lyrics_embedder.py

Fetches lyrics and encodes them into fixed-dimension vectors using CLAP.
"""

import json
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict

# Resolve paths relative to backend root
_THIS_FILE = Path(__file__).resolve()
BACKEND_ROOT = _THIS_FILE.parents[2]  # backend/app/utils → backend

EMBED_CACHE_PATH = BACKEND_ROOT / "app" / "data" / "lyrics_embeddings.json"

# FIXED: Must match the unified 512 CLAP + 3 VAD dimension space
TEXT_DIM = 515

# How many characters of lyrics to pass to CLAP
MAX_CHARS = 1000


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncate to max_chars without cutting mid-word."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > 0 else truncated


class LyricsEmbedder:
    def __init__(self, clap_encoder, target_dim: int = TEXT_DIM):
        """
        clap_encoder : ClapEncoder instance
        target_dim   : output vector size — must match TEXT_DIM in song_store.py
        """
        self.clap = clap_encoder
        self.target_dim = target_dim
        self.cache: Dict = self._load_cache()

    # -----------------------------------------------------------------------
    # Cache helpers
    # -----------------------------------------------------------------------

    def _load_cache(self) -> Dict:
        if not EMBED_CACHE_PATH.exists():
            return {}
        try:
            with open(EMBED_CACHE_PATH, "r", encoding="utf-8") as f:
                raw: Dict = json.load(f)

            # Validate each entry — reject corrupt / old 512-dim embeddings
            clean = {}
            rejected = 0
            for key, entry in raw.items():
                if not isinstance(entry, dict):
                    rejected += 1
                    continue
                emb = entry.get("embedding")
                # UPDATED: Explicitly check that cached items match our new 515 target size
                if not isinstance(emb, list) or len(emb) != self.target_dim:
                    rejected += 1
                    continue
                clean[key] = entry

            if rejected:
                print(
                    f"[LyricsEmbedder] Dropped {rejected} stale/invalid cache entries on load."
                )
            return clean

        except Exception as e:
            print(f"[LyricsEmbedder] Cache load error: {e}")
            return {}

    def _save_cache(self):
        EMBED_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(EMBED_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[LyricsEmbedder] Cache save error: {e}")

    def _cache_key(self, title: str, artist: str) -> str:
        return (
            f"{str(title).lower().strip()}::"
            f"{str(artist).lower().strip()}"
        )

    # -----------------------------------------------------------------------
    # Embedding helpers
    # -----------------------------------------------------------------------

    def _encode_and_resize(self, text: str) -> Optional[np.ndarray]:
        """
        Encodes text with CLAP and resizes the result to target_dim.
        Returns None if the result is a zero vector or has wrong shape.
        """
        try:
            raw = self.clap.encode_text(text)
            emb = np.asarray(raw, dtype=np.float32).flatten()

            # Resize to target_dim (Now beautifully maps to 515)
            if emb.shape[0] > self.target_dim:
                emb = emb[: self.target_dim]
            elif emb.shape[0] < self.target_dim:
                emb = np.pad(emb, (0, self.target_dim - emb.shape[0]))

            # Reject zero vectors — CLAP returned nothing useful
            if np.linalg.norm(emb) < 1e-6:
                print("[LyricsEmbedder] Rejected zero-norm embedding.")
                return None

            return emb

        except Exception as e:
            print(f"[LyricsEmbedder] Encoding error: {e}")
            return None

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def embed_song(self, title: str, artist: str) -> Optional[np.ndarray]:
        """Returns a target_dim-dimensional embedding for the song."""
        from .lyrics_fetcher import LyricsFetcher

        key = self._cache_key(title, artist)

        # Cache hit — re-validate before returning
        cached = self.cache.get(key)
        if cached and isinstance(cached.get("embedding"), list):
            emb = np.array(cached["embedding"], dtype=np.float32)
            if emb.shape[0] == self.target_dim and np.linalg.norm(emb) > 1e-6:
                return emb
            else:
                # Stale / corrupt entry — re-fetch
                print(f"[LyricsEmbedder] Stale cache entry for '{title}' — re-fetching.")
                if key in self.cache:
                    del self.cache[key]

        # Fetch lyrics
        try:
            fetcher = LyricsFetcher()
            lyrics = fetcher.get_lyrics(title, artist)
        except Exception as e:
            print(f"[LyricsEmbedder] Lyrics fetch failed for '{title}': {e}")
            return None

        if not lyrics:
            return None

        # Truncate and encode
        lyrics_chunk = _truncate_at_word(lyrics, MAX_CHARS)
        emb = self._encode_and_resize(lyrics_chunk)

        if emb is None:
            return None

        # Write to cache
        self.cache[key] = {
            "title": title,
            "artist": artist,
            "embedding": emb.tolist(),
            "lyrics_length": len(lyrics),
        }
        self._save_cache()

        return emb

    def embed_many(self, songs: List[Dict]) -> Dict[str, int]:
        """Embeds a list of songs in order."""
        success = skipped = failed = 0

        print(f"[LyricsEmbedder] Starting batch embedding for {len(songs)} songs…")

        for i, song in enumerate(songs, start=1):
            title = song.get("name") or song.get("title") or ""
            artist_raw = song.get("artists") or song.get("artist") or ""

            if isinstance(artist_raw, list):
                artist = artist_raw[0] if artist_raw else "Unknown"
            else:
                artist = str(artist_raw)

            if not title:
                skipped += 1
                continue

            key = self._cache_key(title, artist)
            cached = self.cache.get(key)
            if (
                cached
                and isinstance(cached.get("embedding"), list)
                and len(cached["embedding"]) == self.target_dim
            ):
                skipped += 1
                continue

            print(f"  [{i}/{len(songs)}] {title} — {artist}", end="\r")
            result = self.embed_song(title, artist)

            if result is not None:
                success += 1
            else:
                failed += 1

        summary = {"success": success, "skipped": skipped, "failed": failed}
        print(
            f"\n[LyricsEmbedder] Done. "
            f"Success: {success} | Skipped: {skipped} | Failed: {failed}"
        )
        return summary