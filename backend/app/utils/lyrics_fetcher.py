"""
lyrics_fetcher.py

Fetches and caches song lyrics from Genius.

Fixes:
- Added title match validation before caching — a Genius result that
  doesn't match the requested song is rejected instead of being cached
  under the wrong key (this caused e.g. "Pee Loon" by Pritam getting
  Cape Verdean lyrics cached against it).
- Cache entries are validated on load so stale/corrupt entries are
  silently dropped rather than poisoning embeddings.
- Scraping is more robust against Genius HTML structure changes.
"""

import os
import json
import time
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from typing import Optional

# Resolve backend root regardless of where this file is imported from
_THIS_FILE = Path(__file__).resolve()
BACKEND_ROOT = _THIS_FILE.parents[2]  # backend/app/utils → backend

load_dotenv(dotenv_path=BACKEND_ROOT / ".env")

CACHE_PATH = BACKEND_ROOT / "app" / "data" / "lyrics_cache.json"
GENIUS_SEARCH_URL = "https://api.genius.com/search"

# Minimum ratio of normalised title overlap required to accept a hit
TITLE_MATCH_THRESHOLD = 0.5


class LyricsFetcher:
    def __init__(self, sleep_time: float = 0.4):
        self.sleep_time = sleep_time
        self.token = os.getenv("GENIUS_ACCESS_TOKEN")

        if not self.token:
            raise RuntimeError(
                f"GENIUS_ACCESS_TOKEN not set. Add it to {BACKEND_ROOT / '.env'}"
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

        self.cache = self._load_cache()

    # -----------------------------------------------------------------------
    # Cache helpers
    # -----------------------------------------------------------------------

    def _load_cache(self) -> dict:
        if not CACHE_PATH.exists():
            return {}
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Validate: only keep string values that look like real lyrics
            clean = {
                k: v
                for k, v in raw.items()
                if isinstance(v, str) and len(v.strip()) > 50
            }
            dropped = len(raw) - len(clean)
            if dropped:
                print(f"[LyricsFetcher] Dropped {dropped} invalid cache entries.")
            return clean
        except Exception as e:
            print(f"[LyricsFetcher] Cache read error: {e}")
            return {}

    def _save_cache(self):
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[LyricsFetcher] Cache write error: {e}")

    def _cache_key(self, title: str, artist: str) -> str:
        return f"{self._normalize(title)}::{self._normalize(artist)}"

    # -----------------------------------------------------------------------
    # Text normalisation
    # -----------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, strip bracketed suffixes and punctuation."""
        text = str(text).lower().strip()
        text = re.sub(r"\(.*?\)|- .*?$", "", text)
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    # -----------------------------------------------------------------------
    # Title match validation
    # -----------------------------------------------------------------------

    def _titles_match(self, requested: str, result: str) -> bool:
        """
        Returns True if the Genius result title is close enough to what
        we asked for. Uses word-overlap ratio to handle minor differences
        like featured artists or alternate spellings.

        Example that was failing before:
          requested = "pee loon"
          result    = "na casa nka ta fika"   → rejected ✓
        """
        req_words = set(self._normalize(requested).split())
        res_words = set(self._normalize(result).split())

        if not req_words:
            return False

        overlap = req_words & res_words
        ratio = len(overlap) / len(req_words)
        return ratio >= TITLE_MATCH_THRESHOLD

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_lyrics(self, title: str, artist: str) -> Optional[str]:
        """
        Returns lyrics for the given song, using cache where available.
        Returns None if lyrics can't be found or the match is rejected.
        """
        key = self._cache_key(title, artist)

        cached = self.cache.get(key)
        if cached:
            return cached

        lyrics = self._fetch_from_genius(title, artist)

        if lyrics:
            self.cache[key] = lyrics
            self._save_cache()
            print(f"[LyricsFetcher] Cached: {title} — {artist}")
        else:
            print(f"[LyricsFetcher] Not found: {title} — {artist}")

        time.sleep(self.sleep_time)
        return lyrics

    # -----------------------------------------------------------------------
    # Genius fetch pipeline
    # -----------------------------------------------------------------------

    def _fetch_from_genius(self, title: str, artist: str) -> Optional[str]:
        query = f"{self._normalize(title)} {self._normalize(artist)}"

        try:
            resp = requests.get(
                GENIUS_SEARCH_URL,
                headers=self.headers,
                params={"q": query},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[LyricsFetcher] Genius API error for '{title}': {e}")
            return None

        hits = resp.json().get("response", {}).get("hits", [])
        if not hits:
            return None

        song_url = self._pick_best_hit(hits, title, artist)
        if not song_url:
            return None

        return self._scrape_lyrics(song_url)

    def _pick_best_hit(
        self, hits: list, title: str, artist: str
    ) -> Optional[str]:
        """
        Finds the best matching Genius hit.

        Priority:
          1. Title AND artist both match
          2. Title matches alone
          3. First result (only if title passes the overlap threshold)

        FIX: previously fell through to hits[0] unconditionally, which
             caused completely wrong songs to be cached.
        """
        t_norm = self._normalize(title)
        a_norm = self._normalize(artist)

        best_url = None
        best_score = -1

        for hit in hits:
            res = hit.get("result", {})
            h_title = self._normalize(res.get("title", ""))
            h_artist = self._normalize(
                res.get("primary_artist", {}).get("name", "")
            )

            title_ok = self._titles_match(title, h_title)
            artist_ok = a_norm in h_artist or h_artist in a_norm

            score = (2 if title_ok else 0) + (1 if artist_ok else 0)

            if score > best_score:
                best_score = score
                best_url = res.get("url")

        # Reject entirely if not even the title matched
        if best_score < 2:
            print(
                f"[LyricsFetcher] No confident match for '{title}' by '{artist}' "
                f"(best score={best_score}) — skipping."
            )
            return None

        return best_url

    def _scrape_lyrics(self, url: str) -> Optional[str]:
        """Scrapes lyrics from a Genius song page."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[LyricsFetcher] Scrape error for {url}: {e}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Genius uses data-lyrics-container attribute on current site structure
        containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})

        # Fallback to older class-based selectors
        if not containers:
            containers = soup.select(
                "div[class^='Lyrics__Container'], .lyrics"
            )

        if not containers:
            print(f"[LyricsFetcher] No lyrics container found at {url}")
            return None

        lines = []
        for container in containers:
            # Replace <br> tags with newlines before extracting text
            for br in container.find_all("br"):
                br.replace_with("\n")
            lines.append(container.get_text(separator="\n"))

        raw = "\n".join(lines).strip()
        return self._clean_lyrics(raw)

    @staticmethod
    def _clean_lyrics(lyrics: str) -> str:
        """Removes section headers and normalises whitespace."""
        # Remove [Verse 1], [Chorus], [Intro: Artist] etc.
        lyrics = re.sub(r"\[.*?\]", "", lyrics)
        # Collapse runs of blank lines
        lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)
        return lyrics.strip()