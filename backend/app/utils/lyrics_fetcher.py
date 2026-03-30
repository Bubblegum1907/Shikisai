import os
import json
import time
import re
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import Optional

_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
CACHE_PATH = os.path.join(_backend_root, "data", "lyrics_cache.json")

GENIUS_SEARCH_URL = "https://api.genius.com/search"

class LyricsFetcher:
    def __init__(self, sleep_time: float = 0.4):
        load_dotenv()
        
        self.sleep_time = sleep_time
        
        self.token = os.getenv("GENIUS_ACCESS_TOKEN")
        if not self.token:
            load_dotenv(os.path.join(_backend_root, ".env"))
            self.token = os.getenv("GENIUS_ACCESS_TOKEN")

        if not self.token:
            raise RuntimeError("GENIUS_ACCESS_TOKEN not set in environment")

        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _normalize(self, text: str):
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _cache_key(self, title: str, artist: str):
        return f"{self._normalize(title)}::{self._normalize(artist)}"

    def get_lyrics(self, title: str, artist: str) -> Optional[str]:
        key = self._cache_key(title, artist)

        if key in self.cache:
            return self.cache[key]

        lyrics = self._fetch_lyrics_from_genius(title, artist)

        if lyrics:
            self.cache[key] = lyrics
            self._save_cache()

        time.sleep(self.sleep_time)
        return lyrics

    def _fetch_lyrics_from_genius(self, title: str, artist: str) -> Optional[str]:
        search_query = f"{title} {artist}"

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
        if not song_url:
            return None

        return self._scrape_lyrics_page(song_url)

    def _pick_best_hit(self, hits, title, artist):
        title_norm = title.lower()
        artist_norm = artist.lower()

        for hit in hits:
            result = hit["result"]
            hit_title = result.get("title", "").lower()
            hit_artist = result.get("primary_artist", {}).get("name", "").lower()

            if title_norm in hit_title and artist_norm in hit_artist:
                return result.get("url")

        return hits[0]["result"].get("url")

    def _scrape_lyrics_page(self, url: str) -> Optional[str]:
        try:
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return None

        containers = soup.select("div[data-lyrics-container='true']")

        if not containers:
            alt = soup.find("div", class_="lyrics")
            if alt:
                lyrics = alt.get_text(separator="\n").strip()
                return self._clean_lyrics(lyrics)
            return None

        lyrics_lines = []
        for c in containers:
            lyrics_lines.append(c.get_text(separator="\n"))

        lyrics = "\n".join(lyrics_lines).strip()
        lyrics = self._clean_lyrics(lyrics)

        return lyrics if lyrics else None

    def _clean_lyrics(self, lyrics: str) -> str:
        lyrics = re.sub(r"\[.*?\]", "", lyrics)   
        lyrics = re.sub(r"\n{2,}", "\n", lyrics)  
        return lyrics.strip()