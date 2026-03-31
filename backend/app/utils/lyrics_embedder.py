import os
import json
import numpy as np
import sys
from pathlib import Path
from typing import Optional, List, Dict

# --- 1. DYNAMIC PATH SETUP ---
current_file = Path(__file__).resolve()
backend_root = current_file.parent.parent
sys.path.append(str(backend_root))

# Absolute path for the cache
EMBED_CACHE_PATH = backend_root / "data" / "lyrics_embeddings.json"

# Import your helper
from app.utils.lyrics_fetcher import LyricsFetcher

class LyricsEmbedder:
    def __init__(self, clap_encoder, target_dim: int = 512):
        """
        clap_encoder: Your existing ClapEncoder instance.
        target_dim: Expected vector size for FAISS (default 512).
        """
        self.clap = clap_encoder
        self.fetcher = LyricsFetcher()
        self.target_dim = target_dim
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if EMBED_CACHE_PATH.exists():
            try:
                with open(EMBED_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Embedding cache read error: {e}")
                return {}
        return {}

    def _save_cache(self):
        EMBED_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(EMBED_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Error saving embedding cache: {e}")

    def _cache_key(self, title: str, artist: str) -> str:
        return f"{str(title).lower().strip()}::{str(artist).lower().strip()}"

    def embed_song(self, title: str, artist: str) -> Optional[np.ndarray]:
        """
        Fetches lyrics, encodes them, and ensures they match the target dimension.
        """
        key = self._cache_key(title, artist)

        # 1. Check Cache First
        if key in self.cache and "embedding" in self.cache[key]:
            return np.array(self.cache[key]["embedding"], dtype=np.float32)
        
        # 2. Fetch Lyrics
        try:
            lyrics = self.fetcher.get_lyrics(title, artist)
            if not lyrics:
                return None
        except Exception as e:
            print(f"⚠️ Lyrics fetch failed for {title}: {e}")
            return None

        # 3. Encode Text
        try:
            # CLAP usually prefers a max of 77 tokens, so we keep text concise
            MAX_CHARS = 1000 
            lyrics_short = lyrics[:MAX_CHARS]
            
            # Get raw embedding
            emb = self.clap.encode_text(lyrics_short)
            emb = np.asarray(emb, dtype=np.float32).flatten()

            # 4. Dimension Guard: Force result to target_dim (e.g. 512)
            if emb.shape[0] > self.target_dim:
                emb = emb[:self.target_dim]
            elif emb.shape[0] < self.target_dim:
                pad = np.zeros(self.target_dim - emb.shape[0], dtype=np.float32)
                emb = np.concatenate([emb, pad])

            # 5. Store in Cache
            self.cache[key] = {
                "title": title,
                "artist": artist,
                "embedding": emb.tolist(),
                "lyrics_length": len(lyrics)
            }
            self._save_cache()
            return emb

        except Exception as e:
            print(f"❌ Encoding error for {title}: {e}")
            return None

    def embed_many(self, songs: List[Dict]):
        """
        songs: list of dicts with 'title' and 'artist' keys.
        """
        print(f"🧬 Starting batch embedding for {len(songs)} songs...")
        count = 0
        for s in songs:
            title = s.get("name") or s.get("title") # Handle both naming styles
            artist = s.get("artists") or s.get("artist")
            
            if title and artist:
                result = self.embed_song(title, artist)
                if result is not None:
                    count += 1
        
        print(f"✨ Batch complete. {count} songs successfully embedded.")