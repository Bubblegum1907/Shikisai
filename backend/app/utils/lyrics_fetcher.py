import os
import json
import time
import re
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import Optional

current_file = Path(__file__).resolve()
backend_root = current_file.parent.parent if 'scripts' in current_file.parts else current_file.parent
sys.path.append(str(backend_root))

CACHE_PATH = backend_root / "data" / "lyrics_cache.json"
GENIUS_SEARCH_URL = "https://api.genius.com/search"

class LyricsFetcher:
    def __init__(self, sleep_time: float = 0.4):
        load_dotenv(dotenv_path=backend_root / ".env")
        
        self.sleep_time = sleep_time
        self.token = os.getenv("GENIUS_ACCESS_TOKEN")
        
        if not self.token:
            raise RuntimeError(f"GENIUS_ACCESS_TOKEN not found. Check your .env at {backend_root}")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        self.cache = self._load_cache()

    def _load_cache(self):
        if CACHE_PATH.exists():
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Cache read error: {e}")
                return {}
        return {}

    def _save_cache(self):
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _normalize(self, text: str):
        text = text.lower().strip()
        text = re.sub(r"\(.*?\)|- .*?$", "", text)
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    def _cache_key(self, title: str, artist: str):
        return f"{self._normalize(title)}::{self._normalize(artist)}"

    def get_lyrics(self, title: str, artist: str) -> Optional[str]:
        key = self._cache_key(title, artist)

        if key in self.cache and self.cache[key]:
            return self.cache[key]

        lyrics = self._fetch_lyrics_from_genius(title, artist)

        if lyrics:
            self.cache[key] = lyrics
            self._save_cache()
            print(f"Cached lyrics for: {title}")
        else:
            print(f"Could not find lyrics for: {title}")

        time.sleep(self.sleep_time)
        return lyrics

    def _fetch_lyrics_from_genius(self, title: str, artist: str) -> Optional[str]:
        search_query = f"{self._normalize(title)} {self._normalize(artist)}"

        try:
            r = requests.get(
                GENIUS_SEARCH_URL,
                headers=self.headers, 
                params={"q": search_query},
                timeout=10
            )
            r.raise_for_status()
        except Exception as e:
            print(f"Genius API Error: {e}")
            return None

        hits = r.json().get("response", {}).get("hits", [])
        if not hits:
            return None

        song_url = self._pick_best_hit(hits, title, artist)
        return self._scrape_lyrics_page(song_url) if song_url else None

    def _pick_best_hit(self, hits, title, artist):
        t_norm = self._normalize(title)
        a_norm = self._normalize(artist)

        for hit in hits:
            res = hit["result"]
            h_title = self._normalize(res.get("title", ""))
            h_artist = self._normalize(res.get("primary_artist", {}).get("name", ""))

            if t_norm in h_title and a_norm in h_artist:
                return res.get("url")

        return hits[0]["result"].get("url")

    def _scrape_lyrics_page(self, url: str) -> Optional[str]:
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception:
            return None

        lyrics_lines = []
        containers = soup.select("div[class^='Lyrics__Container'], .lyrics")
        
        if not containers:
            return None

        for c in containers:
            lyrics_lines.append(c.get_text(separator="\n"))

        full_text = "\n".join(lyrics_lines).strip()
        return self._clean_lyrics(full_text)

    def _clean_lyrics(self, lyrics: str) -> str:
        lyrics = re.sub(r"\[.*?\]", "", lyrics) 
        lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)
        return lyrics.strip()