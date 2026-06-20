import os
import ast
import json
import re
import colorsys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRACKS_PATH = os.path.join(DATA_DIR, "my_tracks_with_clap.csv")
LYRICS_PATH = os.path.join(DATA_DIR, "lyrics_embeddings.json")

def normalize_text(s):
    if not isinstance(s, str): return ""
    s = s.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s) 
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return " ".join(s.split())

def hsv_from_hex(hex_color):
    if not hex_color: return 0, 0, 0.5
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v

def resolve_color_emotion(description):
    """
    Parses a string like 'gentle, airy' and returns average V and E targets.
    """
    words = [w.strip().lower() for w in description.replace(',', ' ').split()]
    v_list = []
    e_list = []
    
    for word in words:
        if word in EMOTION_COORDINATES:
            v_list.append(EMOTION_COORDINATES[word]["v"])
            e_list.append(EMOTION_COORDINATES[word]["e"])
            
    final_v = sum(v_list) / len(v_list) if v_list else 0.5
    final_e = sum(e_list) / len(e_list) if e_list else 0.5
    
    return final_v, final_e

def load_and_prep_data():
    if not os.path.exists(TRACKS_PATH):
        raise FileNotFoundError(f"Could not find {TRACKS_PATH}")
    
    df = pd.read_csv(TRACKS_PATH)
    
    def parse_embed(x):
        try:
            arr = np.array(ast.literal_eval(x) if isinstance(x, str) else x, dtype=np.float32)
            if arr.ndim == 1 and len(arr) >= 512 and np.linalg.norm(arr) > 1e-6:
                return arr[:512]
            return None
        except: return None

    df["clap_vec"] = df["clap_embed"].apply(parse_embed)
    df = df[df["clap_vec"].notnull()].reset_index(drop=True)
    
    cols_to_fix = {"valence": 0.5, "energy": 0.5} 
    for col, val in cols_to_fix.items():
        df[col] = df[col].fillna(val) if col in df.columns else val
        
    matrix = np.vstack(df["clap_vec"].values)
    norm_matrix = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
    
    lyrics_data = {}
    if os.path.exists(LYRICS_PATH):
        with open(LYRICS_PATH, "r", encoding="utf-8") as f:
            lyrics_data = json.load(f)
            
    return df, norm_matrix, lyrics_data

df, EMB_NORM, LYRICS_EMBEDDINGS = load_and_prep_data()

def generate_static_vibe_vector(matrix):
    return np.mean(matrix, axis=0)

GLOBAL_VIBE_VECTOR = generate_static_vibe_vector(EMB_NORM)

INTENT_CONFIG = {
    "warm_soft":      {"v_bias": 0.4,  "e_bias": -0.25, "vocal": 0.6,  "inst": 0.6, "clap_w": 0.7,  "cutoff": 0.3},
    "dark_moody":      {"v_bias": -0.6, "e_bias": -0.4,  "vocal": 0.2,  "inst": 0.4, "clap_w": 0.85, "cutoff": 0.4},
    "bold_confident":  {"v_bias": 0.2,  "e_bias": 0.6,   "vocal": 0.25, "inst": 0.15, "clap_w": 1.1,  "cutoff": 0.4},
    "cool_soft":       {"v_bias": 0.0,  "e_bias": -0.35, "vocal": 0.1,  "inst": 0.1, "clap_w": 1.0,  "cutoff": 0.3},
    "bright_playful":  {"v_bias": 0.3,  "e_bias": 0.45,  "vocal": 0.3,  "inst": 0.2, "clap_w": 1.0,  "cutoff": 0.4},
}

EMOTION_COORDINATES = {
    "gentle": {"v": 0.75, "e": 0.25}, "airy": {"v": 0.85, "e": 0.20},
    "soft": {"v": 0.70, "e": 0.20}, "peaceful": {"v": 0.80, "e": 0.15},
    "cheerful": {"v": 0.90, "e": 0.60}, "romantic": {"v": 0.75, "e": 0.30},
    "optimistic": {"v": 0.85, "e": 0.50}, "uplifting": {"v": 0.80, "e": 0.65},
    "fiery": {"v": 0.65, "e": 0.95}, "intense": {"v": 0.50, "e": 0.90},
    "bold": {"v": 0.60, "e": 0.85}, "energetic": {"v": 0.70, "e": 0.90},
    "aggressive": {"v": 0.15, "e": 0.95}, "fierce": {"v": 0.20, "e": 0.90},
    "vibrant": {"v": 0.75, "e": 0.85}, "urgent": {"v": 0.40, "e": 0.90},
    "dark": {"v": 0.15, "e": 0.50}, "heavy": {"v": 0.20, "e": 0.60},
    "brooding": {"v": 0.10, "e": 0.45}, "serious": {"v": 0.30, "e": 0.40},
    "grounded": {"v": 0.50, "e": 0.30}, "introspective": {"v": 0.40, "e": 0.25},
    "mysterious": {"v": 0.35, "e": 0.55}, "quiet": {"v": 0.45, "e": 0.15},
    "dreamy": {"v": 0.60, "e": 0.35}, "nostalgic": {"v": 0.55, "e": 0.30},
    "calm": {"v": 0.65, "e": 0.15}, "serene": {"v": 0.75, "e": 0.15},
    "fresh": {"v": 0.80, "e": 0.40}, "stable": {"v": 0.50, "e": 0.40}
}

COLOR_DESCRIPTIONS = {
  "#FFEBEB": "gentle, airy",
  "#FFCFCF": "soft, tender",
  "#FFB3B3": "romantic, lighthearted",
  "#FF9797": "affectionate, uplifting",
  "#FF7A7A": "warm, lively",
  "#FF5C5C": "passionate, energetic",
  "#FF3E3E": "intense, bold",
  "#FF1F1F": "fiery, urgent",
  "#FF0000": "dominant, powerful",
  "#E50000": "aggressive, fierce",
  "#CC0000": "brooding, dramatic",
  "#B30000": "deep, commanding",
  "#990000": "serious, intense",
  "#800000": "grounded, strong",
  "#660000": "dark, heavy",

  "#FFE5D6": "delicate, warm",
  "#FFD1BB": "gentle, comforting",
  "#FFBC9E": "friendly, approachable",
  "#FFA782": "playful, bright",
  "#FF9366": "social, uplifting",
  "#FF7E4A": "energetic, glowing",
  "#FF692E": "vibrant, bold",
  "#FF550F": "lively, dynamic",
  "#FF4400": "urgent, hot",
  "#E53A00": "fiery, daring",
  "#CC3200": "confident, intense",

  "#FFF3CC": "light, cheerful",
  "#FFE899": "optimistic, soft",
  "#FFDD66": "bright, lively",
  "#FFD233": "happy, playful",
  "#FFC700": "energetic, radiant",
  "#E5B400": "warm, glowing",
  "#CC9F00": "confident, traditional",
  "#B38A00": "grounded, strong",
  "#997700": "serious, earthy",

  "#F7FFCC": "fresh, airy",
  "#ECFF99": "light, hopeful",
  "#E1FF66": "bright, energetic",
  "#D6FF33": "playful, zesty",
  "#CCFF00": "vibrant, lively",
  "#B3E600": "crisp, dynamic",
  "#99CC00": "natural, cheerful",
  "#80B300": "balanced, grounded",
  "#669900": "earthy, stable",
  "#4D8000": "deep, organic",

  "#E8FFD9": "soothing, natural",
  "#CEFFB3": "fresh, gentle",
  "#B5FF8C": "peaceful, optimistic",
  "#9CFF66": "healthy, uplifting",
  "#82FF40": "growth-oriented, bright",
  "#69FF1A": "energetic, lively",
  "#50E600": "vibrant, refreshing",
  "#3ACC00": "steady, confident",
  "#259900": "grounded, stable",
  "#1A6600": "deep, earthy",

  "#D9FFE8": "clean, serene",
  "#B3FFD1": "fresh, balanced",
  "#8CFFBA": "gentle, open",
  "#66FFA3": "smooth, calming",
  "#40FF8C": "easygoing, refreshing",
  "#1AFF75": "bright, energetic",
  "#00E65E": "crisp, vibrant",
  "#00CC52": "focused, steady",
  "#00993D": "grounded, introspective",
  "#006628": "deep, quiet",

  "#D9FFF7": "airy, soft",
  "#B3FFF0": "clear, fresh",
  "#8CFFE8": "smooth, calming",
  "#66FFE0": "cool, bright",
  "#40FFD9": "crisp, refreshing",
  "#1AFFD2": "clean, futuristic",
  "#00E6BF": "energetic, lively",
  "#00CCAA": "crisp, focused",
  "#009988": "deep, cool",
  "#00665C": "introspective, calm",

  "#D9F5FF": "calm, gentle",
  "#B3EBFF": "peaceful, airy",
  "#8CE1FF": "light, fresh",
  "#66D6FF": "open, bright",
  "#40CCFF": "cool, expressive",
  "#1AC2FF": "clear, smooth",
  "#00A9E6": "focused, thoughtful",
  "#008FCC": "deep, stable",
  "#0076B3": "serious, reflective",
  "#005C8C": "quiet, introspective",
  "#003F66": "deep, contemplative",

  "#EBE6FF": "dreamy, nostalgic",
  "#D1CCFF": "soft, thoughtful",
  "#B8B3FF": "gentle, whimsical",
  "#9E99FF": "creative, open",
  "#857FFF": "mystical, expressive",
  "#6C66FF": "imaginative, intuitive",
  "#524CFF": "emotional, deep",
  "#3A33E6": "introspective, serious",
  "#251FCC": "brooding, powerful",
  "#150FB3": "mysterious, dramatic",
  "#0A078A": "dark, contemplative",

  "#FFE6FA": "soft, romantic",
  "#FFCFF5": "tender, dreamy",
  "#FFB8EF": "affectionate, sweet",
  "#FF9EE8": "playful, hopeful",
  "#FF85E1": "expressive, lively",
  "#FF6CDC": "bright, energetic",
  "#FF52D6": "bold, vibrant",
  "#FF33CC": "dynamic, confident",
  "#E600B8": "intense, electric",
  "#B3008A": "deep, emotional",
  "#800066": "mysterious, powerful",

  "#FFF5F7": "pure, gentle",
  "#FFE0E8": "soft, sweet",
  "#FFCCD9": "romantic, tender",
  "#FFB8CB": "warm, affectionate",
  "#FFA3BC": "comforting, uplifting",
  "#FF8EAD": "friendly, bright",
  "#FF799F": "lively, playful",
  "#FF638F": "energetic, expressive",
  "#FF4D7F": "bold, emotional",
  "#CC3A64": "deep, dramatic",
  "#99284A": "serious, passionate",

  "#F2F2F2": "clean, simple",
  "#E0E0E0": "soft, minimal",
  "#CCCCCC": "neutral, calm",
  "#B3B3B3": "balanced, muted",
  "#999999": "steady, quiet",
  "#808080": "grounded, cool",
  "#666666": "serious, deep",
  "#4D4D4D": "focused, introspective",
  "#333333": "mysterious, powerful",
  "#1A1A1A": "dramatic, brooding",
  "#000000": "authoritative, enigmatic",

  "#FFFFFF": "pure, open",
  "#FAFAFA": "light, calm",
  "#F7F7F7": "peaceful, soft",
  "#F0F0F0": "clean, gentle",

  "#FFD7B3": "warm, comforting",
  "#FFC499": "soft, natural",
  "#FFB180": "gentle, human",
  "#FF9E66": "approachable, warm",
  "#E6884D": "grounded, steady",
  "#CC7333": "earthy, stable",
  "#B35E1A": "deep, dignified",
  "#8C4714": "serious, rugged",

  "#F6E8D5": "calm, organic",
  "#E9D3B8": "soft, natural",
  "#D9BA96": "warm, grounded",
  "#C7A47B": "stable, earthy",
  "#B38B5F": "serious, balanced",
  "#9C7647": "deep, rugged",
  "#7A5A33": "strong, steady",
  "#5C4426": "earthy, powerful",

  "#FFD966": "bright, joyful",
  "#FFCC33": "happy, radiant",
  "#FFBF00": "confident, warm",
  "#E6AC00": "traditional, steady",
  "#CC9900": "serious, grounded",
  "#B38600": "rich, warm",

  "#C0C0C0": "sleek, modern",
  "#D4AF37": "luxurious, rich",
  "#B76E79": "romantic, elegant",
  "#B87333": "earthy, bold",
  "#CD7F32": "grounded, strong",
  "#E5E4E2": "refined, pure",

  "#E3F2FD": "calm, airy",
  "#BBDEFB": "light, peaceful",
  "#64B5F6": "open, fresh",
  "#42A5F5": "clear, expressive",
  "#2196F3": "balanced, stable",
  "#1976D2": "serious, thoughtful",
  "#0D47A1": "deep, introspective",

  "#FFCDE3": "tender, sweet",
  "#FFB0D0": "romantic, soft",
  "#FF93BD": "gentle, uplifting",
  "#FF77AB": "expressive, lively",
  "#FF5A98": "bold, emotional",
  "#FF3D86": "dynamic, passionate",
  "#C72E66": "deep, intense",

  "#F3FFE6": "fresh, pure",
  "#DEFFCC": "soft, natural",
  "#C8FFB3": "gentle, balanced",
  "#B3FF99": "healthy, uplifting",
  "#99FF80": "light, optimistic",
  "#80FF66": "energetic, playful",
  "#66CC52": "grounded, stable",

  "#FFE0B3": "warm, soft",
  "#FFC180": "uplifting, bright",
  "#FFA64D": "friendly, lively",
  "#FF8A1A": "energetic, bold",
  "#E67300": "strong, confident",
  "#CC6600": "serious, grounded",

  "#E0F7FA": "clean, airy",
  "#B2EBF2": "cool, calm",
  "#80DEEA": "light, peaceful",
  "#4DD0E1": "open, refreshing",
  "#26C6DA": "smooth, expressive",
  "#00BCD4": "crisp, modern",
  "#0097A7": "deep, introspective"
}

def get_lyric_sim(row, query_norm):
    artist_raw = row["artists"]
    
    try:
        if isinstance(artist_raw, str) and artist_raw.startswith("["):
            artist_list = ast.literal_eval(artist_raw)
            artist = artist_list[0] if len(artist_list) > 0 else "unknown"
        else:
            artist = artist_raw if pd.notnull(artist_raw) else "unknown"
    except (ValueError, SyntaxError, IndexError):
        artist = "unknown"

    key = f"{normalize_text(row['name'])}::{normalize_text(artist)}"
    if key in LYRICS_EMBEDDINGS:
        l_vec = np.array(LYRICS_EMBEDDINGS[key]["embedding"], dtype=np.float32)[:512]
        return np.dot(l_vec, query_norm) / (np.linalg.norm(l_vec) + 1e-9)
    
    return 0.0

def recommend_hybrid(query_embed, hex_color="#FFFFFF", vibe_vector=None, limit=10, v=None, a=None, store=None, **kwargs):
    """
    Dynamically sorts and yields recommendations directly extracted from the 
    live application SongStore tracking matrices.
    """
    # 1. Pipeline Validation Guard
    if store is None or store.vectors is None or not store.metadata:
        return []
        
    # Build dynamic working DataFrame straight from the store's metadata state
    df_active = pd.DataFrame(store.metadata).copy()
    
    # 🚨 FIX: Normalize legacy or mismatched keys on the fly to prevent KeyErrors
    if "name" in df_active.columns and "title" not in df_active.columns:
        df_active = df_active.rename(columns={"name": "title"})
    if "id" in df_active.columns and "spotify_id" not in df_active.columns:
        df_active = df_active.rename(columns={"id": "spotify_id"})
        
    # Extra safety check: if 'title' still isn't there, the metadata is completely blank/corrupt
    if "title" not in df_active.columns:
        print("⚠️ Warning: 'title' column missing from track metadata arrays.")
        return []
    
    clean_hex = hex_color.upper() if hex_color else "#FFFFFF"
    description = COLOR_DESCRIPTIONS.get(clean_hex, "neutral, calm")
    v_target, e_target = resolve_color_emotion(description)

    # Allow custom overrides passed explicitly from main.py
    v_target = v if v is not None else v_target
    e_target = a if a is not None else e_target
    
    query_vec = np.asarray(query_embed, dtype=np.float32).flatten()[:512]
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    
    # 2. Content Blacklist Filters
    # Clean fallback for artists array tracking
    artists_series = df_active["artists"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    text_data = (df_active["title"].fillna("") + " " + artists_series.fillna("")).str.lower()
    
    blacklist = r"soundtrack|ost|theme|zelda|pokémon|final fantasy|game music|bgm"
    allowed = r"anime|animation|drama|tv|opening|ending"
    
    is_ost = text_data.str.contains(blacklist, na=False)
    is_allowed = text_data.str.contains(allowed, na=False)
    
    # Filter out blacklisted gaming tracks unless explicitly whitelisted
    valid_mask = ~(is_ost & ~is_allowed)
    
    # 3. Vector Similarity Calculations
    store_matrix = np.vstack(store.vectors)
    
    # Slice the store matrix down to the first 512 dimensions to match the CLAP text query
    if store_matrix.shape[1] > 512:
        print(f"[RECOMMEND] Slicing store matrix from {store_matrix.shape} down to 512 dimensions for CLAP alignment.")
        store_matrix = store_matrix[:, :512]
        
    store_norm = store_matrix / (np.linalg.norm(store_matrix, axis=1, keepdims=True) + 1e-9)
    
    # Calculate CLAP cosine similarities (Now both are strictly 512)
    clap_scores = np.dot(store_norm, query_norm)
    
    # 4. Hybrid Scoring Aggregation Loop
    final_scores = []
    
    for idx, row in df_active.iterrows():
        if not valid_mask[idx]:
            final_scores.append(-999.0) # Completely suppress blacklisted tracks
            continue
            
        # Base CLAP similarity
        score = clap_scores[idx] * 0.5
        
        # Perceptual Valence/Energy (Arousal) penalty calculation
        track_v = float(row.get("valence", 0.5))
        track_e = float(row.get("energy", 0.5)) # mapping energy to arousal target
        
        v_dist = abs(track_v - v_target)
        e_dist = abs(track_e - e_target)
        
        # Penalize tracks that are emotionally distant from our color frequencies
        score -= (v_dist * 0.15 + e_dist * 0.15)
        
        # Personalization integration if a profile vibe vector exists
        if vibe_vector is not None:
            track_vec = store_norm[idx]
            vibe_sim = np.dot(track_vec, vibe_vector) / (np.linalg.norm(vibe_vector) + 1e-9)
            score += (vibe_sim * 0.2) # Apply 20% taste personalization boost
            
        final_scores.append(score)
        
    # 5. Build Result Payloads
    df_active["_final_score"] = final_scores
    top_tracks = df_active.sort_values(by="_final_score", ascending=False).head(limit)
    
    recommendations = []
    for _, track in top_tracks.iterrows():
        if track["_final_score"] <= -500:
            continue # Skip any blacklisted items
            
        # Parse artists back safely if stored as string lists
        artists_val = track.get("artists", ["Unknown Artist"])
        if isinstance(artists_val, str) and artists_val.startswith("["):
            try:
                artists_val = ast.literal_eval(artists_val)
            except Exception:
                artists_val = [artists_val]
        elif isinstance(artists_val, str):
            artists_val = [artists_val]

        recommendations.append({
            "id": track.get("spotify_id", ""),
            "title": track.get("title", "Unknown Title"),
            "name": track.get("title", "Unknown Title"),
            "artists": artists_val,
            "album": track.get("album", "Unknown Album"),
            "image_url": track.get("image_url", ""),
            "preview_url": track.get("preview_url", None),
            "score": float(track["_final_score"])
        })
        
    return recommendations # This is what was missing!