"""
local_recommender.py

Hybrid recommendation engine combining:
  - CLAP text embedding cosine similarity
  - Valence / Energy (arousal) emotional distance penalty
  - Optional user taste personalisation via vibe vector

FIX: Data is now loaded lazily (only when first needed) instead of at
     module import time. A missing CSV no longer crashes the entire app.
FIX: Single source of truth — recommendations always come from the live
     SongStore passed in, never from a fallback CSV read.
"""

import os
import ast
import json
import re
import colorsys
import numpy as np
import pandas as pd
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
LYRICS_PATH = os.path.join(DATA_DIR, "lyrics_embeddings.json")

# ---------------------------------------------------------------------------
# Lazy-loaded globals — populated on first call to recommend_hybrid
# ---------------------------------------------------------------------------
_LYRICS_EMBEDDINGS: Optional[dict] = None
_data_loaded = False


def _load_lyrics_embeddings() -> dict:
    """Loads lyrics embeddings from disk once, returns empty dict if missing."""
    if not os.path.exists(LYRICS_PATH):
        print(f"[Recommender] No lyrics embeddings found at {LYRICS_PATH} — skipping.")
        return {}
    try:
        with open(LYRICS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[Recommender] Loaded {len(data)} lyrics embeddings.")
        return data
    except Exception as e:
        print(f"[Recommender] Could not load lyrics embeddings: {e}")
        return {}


def _ensure_loaded():
    """Idempotent loader — safe to call multiple times."""
    global _LYRICS_EMBEDDINGS, _data_loaded
    if not _data_loaded:
        _LYRICS_EMBEDDINGS = _load_lyrics_embeddings()
        _data_loaded = True


# ---------------------------------------------------------------------------
# Colour → emotion helpers
# ---------------------------------------------------------------------------

COLOR_DESCRIPTIONS = {
    "#FFEBEB": "gentle, airy",       "#FFCFCF": "soft, tender",
    "#FFB3B3": "romantic, lighthearted", "#FF9797": "affectionate, uplifting",
    "#FF7A7A": "warm, lively",       "#FF5C5C": "passionate, energetic",
    "#FF3E3E": "intense, bold",      "#FF1F1F": "fiery, urgent",
    "#FF0000": "dominant, powerful", "#E50000": "aggressive, fierce",
    "#CC0000": "brooding, dramatic", "#B30000": "deep, commanding",
    "#990000": "serious, intense",   "#800000": "grounded, strong",
    "#660000": "dark, heavy",

    "#FFE5D6": "delicate, warm",     "#FFD1BB": "gentle, comforting",
    "#FFBC9E": "friendly, approachable", "#FFA782": "playful, bright",
    "#FF9366": "social, uplifting",  "#FF7E4A": "energetic, glowing",
    "#FF692E": "vibrant, bold",      "#FF550F": "lively, dynamic",
    "#FF4400": "urgent, hot",        "#E53A00": "fiery, daring",
    "#CC3200": "confident, intense",

    "#FFF3CC": "light, cheerful",    "#FFE899": "optimistic, soft",
    "#FFDD66": "bright, lively",     "#FFD233": "happy, playful",
    "#FFC700": "energetic, radiant", "#E5B400": "warm, glowing",
    "#CC9F00": "confident, traditional", "#B38A00": "grounded, strong",
    "#997700": "serious, earthy",

    "#F7FFCC": "fresh, airy",        "#ECFF99": "light, hopeful",
    "#E1FF66": "bright, energetic",  "#D6FF33": "playful, zesty",
    "#CCFF00": "vibrant, lively",    "#B3E600": "crisp, dynamic",
    "#99CC00": "natural, cheerful",  "#80B300": "balanced, grounded",
    "#669900": "earthy, stable",     "#4D8000": "deep, organic",

    "#E8FFD9": "soothing, natural",  "#CEFFB3": "fresh, gentle",
    "#B5FF8C": "peaceful, optimistic", "#9CFF66": "healthy, uplifting",
    "#82FF40": "growth-oriented, bright", "#69FF1A": "energetic, lively",
    "#50E600": "vibrant, refreshing", "#3ACC00": "steady, confident",
    "#259900": "grounded, stable",   "#1A6600": "deep, earthy",

    "#D9FFE8": "clean, serene",      "#B3FFD1": "fresh, balanced",
    "#8CFFBA": "gentle, open",       "#66FFA3": "smooth, calming",
    "#40FF8C": "easygoing, refreshing", "#1AFF75": "bright, energetic",
    "#00E65E": "crisp, vibrant",     "#00CC52": "focused, steady",
    "#00993D": "grounded, introspective", "#006628": "deep, quiet",

    "#D9FFF7": "airy, soft",         "#B3FFF0": "clear, fresh",
    "#8CFFE8": "smooth, calming",    "#66FFE0": "cool, bright",
    "#40FFD9": "crisp, refreshing",  "#1AFFD2": "clean, futuristic",
    "#00E6BF": "energetic, lively",  "#00CCAA": "crisp, focused",
    "#009988": "deep, cool",         "#00665C": "introspective, calm",

    "#D9F5FF": "calm, gentle",       "#B3EBFF": "peaceful, airy",
    "#8CE1FF": "light, fresh",       "#66D6FF": "open, bright",
    "#40CCFF": "cool, expressive",   "#1AC2FF": "clear, smooth",
    "#00A9E6": "focused, thoughtful", "#008FCC": "deep, stable",
    "#0076B3": "serious, reflective", "#005C8C": "quiet, introspective",
    "#003F66": "deep, contemplative",

    "#EBE6FF": "dreamy, nostalgic",  "#D1CCFF": "soft, thoughtful",
    "#B8B3FF": "gentle, whimsical",  "#9E99FF": "creative, open",
    "#857FFF": "mystical, expressive", "#6C66FF": "imaginative, intuitive",
    "#524CFF": "emotional, deep",    "#3A33E6": "introspective, serious",
    "#251FCC": "brooding, powerful", "#150FB3": "mysterious, dramatic",
    "#0A078A": "dark, contemplative",

    "#FFE6FA": "soft, romantic",     "#FFCFF5": "tender, dreamy",
    "#FFB8EF": "affectionate, sweet", "#FF9EE8": "playful, hopeful",
    "#FF85E1": "expressive, lively", "#FF6CDC": "bright, energetic",
    "#FF52D6": "bold, vibrant",      "#FF33CC": "dynamic, confident",
    "#E600B8": "intense, electric",  "#B3008A": "deep, emotional",
    "#800066": "mysterious, powerful",

    "#FFF5F7": "pure, gentle",       "#FFE0E8": "soft, sweet",
    "#FFCCD9": "romantic, tender",   "#FFB8CB": "warm, affectionate",
    "#FFA3BC": "comforting, uplifting", "#FF8EAD": "friendly, bright",
    "#FF799F": "lively, playful",    "#FF638F": "energetic, expressive",
    "#FF4D7F": "bold, emotional",    "#CC3A64": "deep, dramatic",
    "#99284A": "serious, passionate",

    "#F2F2F2": "clean, simple",      "#E0E0E0": "soft, minimal",
    "#CCCCCC": "neutral, calm",      "#B3B3B3": "balanced, muted",
    "#999999": "steady, quiet",      "#808080": "grounded, cool",
    "#666666": "serious, deep",      "#4D4D4D": "focused, introspective",
    "#333333": "mysterious, powerful", "#1A1A1A": "dramatic, brooding",
    "#000000": "authoritative, enigmatic",

    "#FFFFFF": "pure, open",         "#FAFAFA": "light, calm",
    "#F7F7F7": "peaceful, soft",     "#F0F0F0": "clean, gentle",

    "#FFD7B3": "warm, comforting",   "#FFC499": "soft, natural",
    "#FFB180": "gentle, human",      "#FF9E66": "approachable, warm",
    "#E6884D": "grounded, steady",   "#CC7333": "earthy, stable",
    "#B35E1A": "deep, dignified",    "#8C4714": "serious, rugged",

    "#F6E8D5": "calm, organic",      "#E9D3B8": "soft, natural",
    "#D9BA96": "warm, grounded",     "#C7A47B": "stable, earthy",
    "#B38B5F": "serious, balanced",  "#9C7647": "deep, rugged",
    "#7A5A33": "strong, steady",     "#5C4426": "earthy, powerful",

    "#FFD966": "bright, joyful",     "#FFCC33": "happy, radiant",
    "#FFBF00": "confident, warm",    "#E6AC00": "traditional, steady",
    "#CC9900": "serious, grounded",  "#B38600": "rich, warm",

    "#C0C0C0": "sleek, modern",      "#D4AF37": "luxurious, rich",
    "#B76E79": "romantic, elegant",  "#B87333": "earthy, bold",
    "#CD7F32": "grounded, strong",   "#E5E4E2": "refined, pure",

    "#E3F2FD": "calm, airy",         "#BBDEFB": "light, peaceful",
    "#64B5F6": "open, fresh",        "#42A5F5": "clear, expressive",
    "#2196F3": "balanced, stable",   "#1976D2": "serious, thoughtful",
    "#0D47A1": "deep, introspective",

    "#FFCDE3": "tender, sweet",      "#FFB0D0": "romantic, soft",
    "#FF93BD": "gentle, uplifting",  "#FF77AB": "expressive, lively",
    "#FF5A98": "bold, emotional",    "#FF3D86": "dynamic, passionate",
    "#C72E66": "deep, intense",

    "#F3FFE6": "fresh, pure",        "#DEFFCC": "soft, natural",
    "#C8FFB3": "gentle, balanced",   "#B3FF99": "healthy, uplifting",
    "#99FF80": "light, optimistic",  "#80FF66": "energetic, playful",
    "#66CC52": "grounded, stable",

    "#FFE0B3": "warm, soft",         "#FFC180": "uplifting, bright",
    "#FFA64D": "friendly, lively",   "#FF8A1A": "energetic, bold",
    "#E67300": "strong, confident",  "#CC6600": "serious, grounded",

    "#E0F7FA": "clean, airy",        "#B2EBF2": "cool, calm",
    "#80DEEA": "light, peaceful",    "#4DD0E1": "open, refreshing",
    "#26C6DA": "smooth, expressive", "#00BCD4": "crisp, modern",
    "#0097A7": "deep, introspective",
}

EMOTION_COORDINATES = {
    "gentle":        {"v": 0.75, "e": 0.25},
    "airy":          {"v": 0.85, "e": 0.20},
    "soft":          {"v": 0.70, "e": 0.20},
    "tender":        {"v": 0.72, "e": 0.22},
    "peaceful":      {"v": 0.80, "e": 0.15},
    "serene":        {"v": 0.75, "e": 0.15},
    "calm":          {"v": 0.65, "e": 0.15},
    "quiet":         {"v": 0.45, "e": 0.15},
    "dreamy":        {"v": 0.60, "e": 0.35},
    "nostalgic":     {"v": 0.55, "e": 0.30},
    "romantic":      {"v": 0.75, "e": 0.30},
    "warm":          {"v": 0.70, "e": 0.35},
    "fresh":         {"v": 0.80, "e": 0.40},
    "cheerful":      {"v": 0.90, "e": 0.60},
    "optimistic":    {"v": 0.85, "e": 0.50},
    "uplifting":     {"v": 0.80, "e": 0.65},
    "playful":       {"v": 0.85, "e": 0.55},
    "bright":        {"v": 0.88, "e": 0.60},
    "happy":         {"v": 0.90, "e": 0.65},
    "lively":        {"v": 0.80, "e": 0.70},
    "vibrant":       {"v": 0.75, "e": 0.85},
    "energetic":     {"v": 0.70, "e": 0.90},
    "bold":          {"v": 0.60, "e": 0.85},
    "confident":     {"v": 0.65, "e": 0.75},
    "fiery":         {"v": 0.65, "e": 0.95},
    "intense":       {"v": 0.50, "e": 0.90},
    "urgent":        {"v": 0.40, "e": 0.90},
    "aggressive":    {"v": 0.15, "e": 0.95},
    "fierce":        {"v": 0.20, "e": 0.90},
    "dominant":      {"v": 0.40, "e": 0.85},
    "powerful":      {"v": 0.45, "e": 0.80},
    "dark":          {"v": 0.15, "e": 0.50},
    "heavy":         {"v": 0.20, "e": 0.60},
    "brooding":      {"v": 0.10, "e": 0.45},
    "dramatic":      {"v": 0.30, "e": 0.65},
    "serious":       {"v": 0.30, "e": 0.40},
    "grounded":      {"v": 0.50, "e": 0.30},
    "stable":        {"v": 0.50, "e": 0.40},
    "introspective": {"v": 0.40, "e": 0.25},
    "mysterious":    {"v": 0.35, "e": 0.55},
    "deep":          {"v": 0.30, "e": 0.35},
    "contemplative": {"v": 0.35, "e": 0.20},
    "focused":       {"v": 0.55, "e": 0.50},
    "cool":          {"v": 0.60, "e": 0.30},
    "clean":         {"v": 0.65, "e": 0.40},
    "crisp":         {"v": 0.70, "e": 0.55},
    "smooth":        {"v": 0.65, "e": 0.35},
    "open":          {"v": 0.70, "e": 0.45},
    "balanced":      {"v": 0.55, "e": 0.45},
    "natural":       {"v": 0.60, "e": 0.35},
    "earthy":        {"v": 0.50, "e": 0.35},
    "pure":          {"v": 0.75, "e": 0.30},
    "sleek":         {"v": 0.60, "e": 0.50},
    "luxurious":     {"v": 0.65, "e": 0.40},
    "electric":      {"v": 0.55, "e": 0.92},
    "emotional":     {"v": 0.45, "e": 0.60},
    "futuristic":    {"v": 0.60, "e": 0.65},
    "whimsical":     {"v": 0.75, "e": 0.50},
    "imaginative":   {"v": 0.70, "e": 0.55},
    "expressive":    {"v": 0.65, "e": 0.65},
    "dynamic":       {"v": 0.65, "e": 0.80},
    "easygoing":     {"v": 0.72, "e": 0.30},
    "comforting":    {"v": 0.72, "e": 0.28},
    "affectionate":  {"v": 0.78, "e": 0.32},
    "social":        {"v": 0.80, "e": 0.60},
    "passionate":    {"v": 0.70, "e": 0.80},
    "commanding":    {"v": 0.45, "e": 0.75},
    "authoritative": {"v": 0.40, "e": 0.70},
    "enigmatic":     {"v": 0.35, "e": 0.55},
    "rugged":        {"v": 0.45, "e": 0.55},
    "dignified":     {"v": 0.55, "e": 0.35},
    "refined":       {"v": 0.65, "e": 0.35},
    "minimal":       {"v": 0.55, "e": 0.20},
    "muted":         {"v": 0.50, "e": 0.25},
    "organic":       {"v": 0.58, "e": 0.32},
    "rich":          {"v": 0.60, "e": 0.45},
    "joyful":        {"v": 0.95, "e": 0.70},
    "radiant":       {"v": 0.88, "e": 0.72},
    "glowing":       {"v": 0.82, "e": 0.68},
    "daring":        {"v": 0.58, "e": 0.88},
    "zesty":         {"v": 0.85, "e": 0.72},
    "hopeful":       {"v": 0.82, "e": 0.48},
    "delicate":      {"v": 0.74, "e": 0.18},
    "approachable":  {"v": 0.76, "e": 0.48},
    "friendly":      {"v": 0.82, "e": 0.52},
    "healthy":       {"v": 0.75, "e": 0.50},
    "steady":        {"v": 0.55, "e": 0.38},
    "traditional":   {"v": 0.58, "e": 0.38},
    "thoughtful":    {"v": 0.52, "e": 0.30},
    "reflective":    {"v": 0.48, "e": 0.25},
    "modern":        {"v": 0.62, "e": 0.55},
    "elegant":       {"v": 0.68, "e": 0.32},
}


def _normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s)
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return " ".join(s.split())


def _resolve_color_emotion(description: str):
    """
    Parses a comma-separated emotion string like 'gentle, airy'
    and returns the average (valence, energy) targets.
    Falls back to neutral (0.5, 0.5) for unknown words.
    """
    words = [w.strip().lower() for w in description.replace(",", " ").split()]
    v_list, e_list = [], []

    for word in words:
        coords = EMOTION_COORDINATES.get(word)
        if coords:
            v_list.append(coords["v"])
            e_list.append(coords["e"])

    v = sum(v_list) / len(v_list) if v_list else 0.5
    e = sum(e_list) / len(e_list) if e_list else 0.5
    return v, e


def _nearest_hex(hex_color: str) -> str:
    """
    Returns the nearest key from COLOR_DESCRIPTIONS using RGB distance.
    Used as a fallback when the exact hex isn't in the map.
    """
    hex_color = hex_color.upper().lstrip("#")
    try:
        r1, g1, b1 = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    except (ValueError, IndexError):
        return "#808080"

    best_key, best_dist = "#808080", float("inf")
    for key in COLOR_DESCRIPTIONS:
        kh = key.lstrip("#")
        try:
            r2, g2, b2 = int(kh[0:2], 16), int(kh[2:4], 16), int(kh[4:6], 16)
            dist = (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2
            if dist < best_dist:
                best_dist, best_key = dist, key
        except (ValueError, IndexError):
            continue
    return best_key


def _get_lyric_sim(title: str, artist: str, query_norm: np.ndarray) -> float:
    """Returns cosine similarity between lyrics embedding and query, or 0.0."""
    _ensure_loaded()
    key = f"{_normalize_text(title)}::{_normalize_text(artist)}"
    entry = _LYRICS_EMBEDDINGS.get(key)  # type: ignore[union-attr]
    if entry is None:
        return 0.0
    try:
        l_vec = np.array(entry["embedding"], dtype=np.float32)[:512]
        norm = np.linalg.norm(l_vec)
        if norm < 1e-9:
            return 0.0
        return float(np.dot(l_vec / norm, query_norm))
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def recommend_hybrid(
    query_embed: np.ndarray,
    hex_color: str = "#FFFFFF",
    vibe_vector: Optional[np.ndarray] = None,
    limit: int = 10,
    v: Optional[float] = None,
    a: Optional[float] = None,
    store=None,
    **kwargs,
) -> list:
    """
    Returns up to `limit` recommendations from the live SongStore.

    Single source of truth: only the SongStore passed in is used.
    No CSV fallback — if the store is empty, an empty list is returned
    and the caller should check /indexing_status.
    """
    _ensure_loaded()

    # Guard: store must be populated
    if store is None or store.vectors is None or not store.metadata:
        print("[Recommender] Store is empty — returning no results.")
        return []

    # -----------------------------------------------------------------------
    # 1. Resolve colour → emotional targets
    # -----------------------------------------------------------------------
    clean_hex = hex_color.upper() if hex_color else "#FFFFFF"
    description = COLOR_DESCRIPTIONS.get(
        clean_hex,
        COLOR_DESCRIPTIONS.get(_nearest_hex(clean_hex), "neutral, calm"),
    )
    v_target, e_target = _resolve_color_emotion(description)

    # Allow explicit overrides passed from main.py
    v_target = v if v is not None else v_target
    e_target = a if a is not None else e_target

    # -----------------------------------------------------------------------
    # 2. Normalise query vector
    # -----------------------------------------------------------------------
    query_vec = np.asarray(query_embed, dtype=np.float32).flatten()[:512]
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-9)

    # -----------------------------------------------------------------------
    # 3. Build working DataFrame from store metadata
    # -----------------------------------------------------------------------
    df = pd.DataFrame(store.metadata).copy()

    # Normalise column names — store uses 'title', older entries may use 'name'
    if "name" in df.columns and "title" not in df.columns:
        df = df.rename(columns={"name": "title"})
    if "id" in df.columns and "spotify_id" not in df.columns:
        df = df.rename(columns={"id": "spotify_id"})

    if "title" not in df.columns:
        print("[Recommender] Metadata is missing 'title' column — returning no results.")
        return []

    # -----------------------------------------------------------------------
    # 4. CLAP cosine similarities
    # -----------------------------------------------------------------------
    store_matrix = np.vstack(store.vectors).astype(np.float32)

    # Align to 512 dims to match the query
    if store_matrix.shape[1] > 512:
        store_matrix = store_matrix[:, :512]

    norms = np.linalg.norm(store_matrix, axis=1, keepdims=True) + 1e-9
    store_norm = store_matrix / norms
    clap_scores = store_norm @ query_norm  # shape: (N,)

    # -----------------------------------------------------------------------
    # 5. Normalise vibe vector once if present
    # -----------------------------------------------------------------------
    vibe_norm = None
    if vibe_vector is not None:
        vv = np.asarray(vibe_vector, dtype=np.float32).flatten()[:512]
        vn = np.linalg.norm(vv)
        if vn > 1e-9:
            vibe_norm = vv / vn

    # -----------------------------------------------------------------------
    # 6. Blacklist filter
    # -----------------------------------------------------------------------
    artists_series = df["artists"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    text_data = (df["title"].fillna("") + " " + artists_series.fillna("")).str.lower()

    blacklist_pat = r"soundtrack|ost|theme|zelda|pokémon|final fantasy|game music|bgm"
    allow_pat = r"anime|animation|drama|tv|opening|ending"

    is_ost = text_data.str.contains(blacklist_pat, na=False)
    is_allowed = text_data.str.contains(allow_pat, na=False)
    valid_mask = ~(is_ost & ~is_allowed)

    # -----------------------------------------------------------------------
    # 7. Score every track
    # -----------------------------------------------------------------------
    scores = np.zeros(len(df), dtype=np.float32)

    for idx in range(len(df)):
        if not valid_mask.iloc[idx]:
            scores[idx] = -999.0
            continue

        # Base: CLAP similarity (50 % weight)
        score = float(clap_scores[idx]) * 0.5

        # Emotional distance penalty
        row = df.iloc[idx]
        track_v = float(row.get("valence", 0.5))
        track_e = float(row.get("energy", 0.5))
        score -= abs(track_v - v_target) * 0.15
        score -= abs(track_e - e_target) * 0.15

        # Lyrics similarity bonus (up to +0.10)
        title = str(row.get("title", ""))
        artist_raw = row.get("artists", "")
        artist = (
            artist_raw[0]
            if isinstance(artist_raw, list) and artist_raw
            else str(artist_raw)
        )
        lyric_sim = _get_lyric_sim(title, artist, query_norm)
        score += lyric_sim * 0.10

        # Personalisation boost (up to +0.20)
        if vibe_norm is not None:
            track_vec = store_norm[idx]
            vibe_sim = float(np.dot(track_vec, vibe_norm))
            score += vibe_sim * 0.20

        scores[idx] = score

    # -----------------------------------------------------------------------
    # 8. Rank and build output
    # -----------------------------------------------------------------------
    top_indices = np.argsort(scores)[::-1][:limit]

    recommendations = []
    for idx in top_indices:
        if scores[idx] <= -500:
            continue

        row = df.iloc[idx]
        artists_val = row.get("artists", ["Unknown Artist"])
        if isinstance(artists_val, str):
            if artists_val.startswith("["):
                try:
                    artists_val = ast.literal_eval(artists_val)
                except Exception:
                    artists_val = [artists_val]
            else:
                artists_val = [artists_val]

        recommendations.append({
            "id": row.get("spotify_id", ""),
            "name": row.get("title", "Unknown Title"),
            "artists": artists_val,
            "album": row.get("album", ""),
            "image_url": row.get("image_url", ""),
            "preview_url": row.get("preview_url", None),
            "valence": float(row.get("valence", 0.5)),
            "energy": float(row.get("energy", 0.5)),
            "score": float(scores[idx]),
        })

    return recommendations