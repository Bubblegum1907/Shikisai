import os
import json
import numpy as np
from typing import Optional

from app.utils.lyrics_fetcher import LyricsFetcher


EMBED_CACHE_PATH = os.path.join("data", "lyrics_embeddings.json")


class LyricsEmbedder:
    def __init__(self, clap_encoder):
        """
        clap_encoder: your existing ClapEncoder instance
        """
        self.clap = clap_encoder
        self.fetcher = LyricsFetcher()
        self.cache = self._load_cache()

    # Cache helpers
    def _load_cache(self):
        if os.path.exists(EMBED_CACHE_PATH):
            try:
                with open(EMBED_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(EMBED_CACHE_PATH), exist_ok=True)
        with open(EMBED_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _cache_key(self, title: str, artist: str):
        return f"{title.lower().strip()}::{artist.lower().strip()}"

    # Public API
    def embed_song(self, title: str, artist: str) -> Optional[np.ndarray]:
        """
        Fetch lyrics (cached), embed them with CLAP, and store result.
        Returns embedding or None.
        """
        key = self._cache_key(title, artist)

        # already embedded
        if key in self.cache:
            emb = np.array(self.cache[key]["embedding"], dtype=np.float32)
            return emb
        
        lyrics = self.fetcher.get_lyrics(title, artist)
        if not lyrics:
            return None
        
        print("Lyrics length:", len(lyrics) if lyrics else "None")


        # Encode lyrics text
        MAX_CHARS = 1000   # safe for CLAP text encoder
        lyrics_short = lyrics[:MAX_CHARS]
        emb = self.clap.encode_text(lyrics_short)
        emb = np.asarray(emb, dtype=np.float32)

        # CLAP safety: enforce 512-dim
        if emb.shape[0] > 512:
            emb = emb[:512]
        elif emb.shape[0] < 512:
            pad = np.zeros(512 - emb.shape[0], dtype=np.float32)
            emb = np.concatenate([emb, pad])

        # Save to cache
        self.cache[key] = {
            "title": title,
            "artist": artist,
            "embedding": emb.tolist(),
            "lyrics_length": len(lyrics)
        }
        self._save_cache()

        return emb

    # Batch helper
    def embed_many(self, songs):
        """
        songs: list of dicts with 'title' and 'artist'
        """
        for s in songs:
            title = s.get("title")
            artist = s.get("artist")
            if title and artist:
                self.embed_song(title, artist)
