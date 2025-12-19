import os
import ast
import numpy as np
import pandas as pd
import colorsys
import re

BLACKLIST_KEYWORDS = [
    "soundtrack", "ost", "original soundtrack", "theme", 
    "opening", "ending", "legend of zelda", "pokémon",
    "final fantasy", "piano", "instrumental", "score"
    "title theme", "end credits", "main theme",
    "felt piano", "piano version", "piano cover",
    "instrumental", "game music", "bgm", "sleepy piano"
]

# LOAD DATASET
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE_PATH = os.path.join(DATA_DIR, "my_tracks_with_clap.csv")

df = pd.read_csv(FILE_PATH)


# SAFE UTILITIES
def parse_list(x):
    if isinstance(x, str) and x.startswith("["):
        try:
            return ast.literal_eval(x)
        except:
            return []
    return x if isinstance(x, list) else []


def safe_parse_embed(x):
    """
    Parse CLAP embedding safely.
    Return None if invalid.
    """
    if isinstance(x, str):
        try:
            arr = np.array(ast.literal_eval(x), dtype=np.float32)
            if arr.ndim == 1 and len(arr) > 10 and np.linalg.norm(arr) > 1e-6:
                return arr
            return None
        except:
            return None

    if isinstance(x, list):
        arr = np.array(x, dtype=np.float32)
        return arr if np.linalg.norm(arr) > 1e-6 else None

    return None


# FIX GENRES + EMBEDDINGS
if "genres" not in df.columns:
    df["genres"] = [[] for _ in range(len(df))]
else:
    df["genres"] = df["genres"].apply(parse_list)

df["clap_vec"] = df["clap_embed"].apply(safe_parse_embed)

# REMOVE SONGS WITH INVALID EMBEDDINGS
df = df[df["clap_vec"].notnull()].reset_index(drop=True)

print("After filtering invalid embeddings:", len(df))

if len(df) == 0:
    raise ValueError("No valid CLAP embeddings found — check your CSV formatting!")

# FIX NUMERICAL FIELDS
df["valence"] = df["valence"].fillna(0.5)
df["energy"] = df["energy"].fillna(0.5)
df["instrumentalness"] = df["instrumentalness"].fillna(0.0)
df["speechiness"] = df["speechiness"].fillna(0.05)
df["popularity"] = df["popularity"].fillna(0.0)
df["release_year"] = df["release_year"].fillna(2010).astype(int)

# PRECOMPUTE NORMALIZED EMBEDDING MATRIX
EMB_MATRIX = np.vstack(df["clap_vec"].values).astype(np.float32)
EMB_MATRIX = EMB_MATRIX[:, :512]   # 🔒 FIX
EMB_NORM = EMB_MATRIX / (np.linalg.norm(EMB_MATRIX, axis=1, keepdims=True) + 1e-9)


# COSINE SIMILARITY
def cosine_sim_np(vec):
    if vec is None:
        return np.zeros(len(df))

    vec = np.array(vec, dtype=np.float32)[:512]
    vec_norm = vec / (np.linalg.norm(vec) + 1e-9)

    return EMB_NORM @ vec_norm


# COLOR → INTENT LAYER
def hsv_from_hex(hex_color):
    if not hex_color:
        return 0, 0, 0.5

    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i+2], 16)/255 for i in (0,2,4)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v


INTENT_CONFIG = {
    "warm_soft": {
        "vocal_boost": 0.6,
        "instrumental_penalty": 0.6,
        "energy_bias": -0.25,
        "valence_bias": +0.4,
        "clap_weight": 0.7,
    },
    "bright_playful": {
        "vocal_boost": 0.3,
        "instrumental_penalty": 0.2,
        "energy_bias": +0.45,
        "valence_bias": +0.3,
        "clap_weight": 1.0,
    },
    "cool_soft": {
        "vocal_boost": 0.1,
        "instrumental_penalty": 0.1,
        "energy_bias": -0.35,
        "valence_bias": 0.0,
        "clap_weight": 1.0,
    },
    "melancholy_soft": {
        "vocal_boost": 0.2,
        "instrumental_penalty": 0.2,
        "energy_bias": -0.4,
        "valence_bias": -0.35,
        "clap_weight": 0.9,
    },
    "dark_moody": {
        "vocal_boost": 0.2,
        "instrumental_penalty": 0.4,
        "energy_bias": -0.15,
        "valence_bias": -0.4,
        "clap_weight": 0.85,
    },
    "bold_confident": {
        "vocal_boost": 0.25,
        "instrumental_penalty": 0.15,
        "energy_bias": +0.6,
        "valence_bias": +0.2,
        "clap_weight": 1.1,
    },
    "nostalgic_warm": {
        "vocal_boost": 0.35,
        "instrumental_penalty": 0.25,
        "energy_bias": -0.15,
        "valence_bias": +0.1,
        "clap_weight": 0.9,
    },
    "romantic_dreamy": {
        "vocal_boost": 0.5,
        "instrumental_penalty": 0.3,
        "energy_bias": -0.1,
        "valence_bias": +0.25,
        "clap_weight": 0.85,
    },
    "mystical_ambient": {
        "vocal_boost": 0.0,
        "instrumental_penalty": 0.0,
        "energy_bias": -0.5,
        "valence_bias": 0.0,
        "clap_weight": 1.0,
    },
    "chaotic_energy": {
        "vocal_boost": 0.1,
        "instrumental_penalty": 0.0,
        "energy_bias": +0.9,
        "valence_bias": 0.0,
        "clap_weight": 1.1,
    },
}


def color_to_intent(hex_color):
    h, s, v = hsv_from_hex(hex_color)

    if s < 0.2 and v > 0.7:
        return "warm_soft"

    if 70 <= h <= 150 and s > 0.4:
        return "bright_playful"

    if 200 <= h <= 260 and s < 0.4:
        return "cool_soft"

    if v < 0.25:
        return "dark_moody"

    if s < 0.25 and v < 0.6:
        return "melancholy_soft"

    if 0 <= h <= 20 and s > 0.6:
        return "bold_confident"

    if 20 <= h <= 60 and s < 0.4:
        return "nostalgic_warm"

    if 260 <= h <= 320:
        return "romantic_dreamy"

    if s < 0.15:
        return "mystical_ambient"

    return "cool_soft"


# FINAL HYBRID RECOMMENDER
def recommend_hybrid(
    query_embed,
    v,
    a,
    hex_color=None,
    user_taste=None,
    preferences=None,
    limit=10,
    df_subset=None
):

    ALLOW_TERMS = [
        "anime", "animation", "op", "ed",
        "opening", "ending",
        "drama", "tv", "television",
        "k-drama", "kdrama", "c-drama", "cdrama", "j-drama",
        "电视剧", "動畫", "アニメ", "片尾曲", "插曲"
    ]
    # SAFETY
    query_embed = np.asarray(query_embed, dtype=np.float32)[:512]
    assert query_embed.shape[0] == 512, f"BAD QUERY EMBED SHAPE: {query_embed.shape}"

    # USER PROFILE
    user_profile = {
        "energy_pref": 0.3,
        "instrumental_pref": 0.2,
        "popularity_pref": 0.6,
        "avoid_game_ost": True,
    }

    if preferences is None:
        preferences = {
            "w_clap": 1.0,
            "w_emotion": 1.0,
            "w_modern": 0.5,
            "w_energy_pref": 0.3,
        }

    df2 = df_subset.copy() if df_subset is not None else df.copy()

    # HARD OST / INSTRUMENTAL PURGE
    blacklist_pattern = "|".join(BLACKLIST_KEYWORDS)

    text_all = (
        df2["name"].str.lower() + " " +
        df2["artists"].astype(str).str.lower()
    )

    is_blacklisted = text_all.str.contains(blacklist_pattern, na=False)

    is_allowed = text_all.str.contains(
        "|".join(ALLOW_TERMS),
        na=False
    )

    is_real_instrumental = df2["instrumentalness"] > 0.75

    df2 = df2[~(is_blacklisted & is_real_instrumental & ~is_allowed)]

    intent = color_to_intent(hex_color)
    cfg = INTENT_CONFIG[intent]


    w_clap = preferences["w_clap"] * cfg["clap_weight"]
    w_emo = preferences["w_emotion"]
    w_mod = preferences["w_modern"]
    w_energy_pref = preferences["w_energy_pref"]

    # EMOTION SCORE
    a = 0.7 * a + 0.3 * user_profile["energy_pref"]
    emotion_dist = np.sqrt(
        (df2["valence"] - v) ** 2 +
        (df2["energy"] - a) ** 2
    )

    df2["emotion_score"] = np.exp(-3.5 * emotion_dist)

    cutoff = {
        "warm_soft": 0.45,
        "cool_soft": 0.42,
        "dark_moody": 0.40
    }.get(intent, 0.45)

    df2 = df2[emotion_dist < cutoff]

     
    # CLAP SIMILARITY
    clap_sim_all = cosine_sim_np(query_embed)
    df2["clap_sim"] = clap_sim_all[df2.index]
        
    # METADATA NORMALIZATION
    df2["pop_norm"] = df2["popularity"] / 100
    df2["year_norm"] = ((df2["release_year"] - 1990) / 35).clip(0, 1)
      
    # BASE SCORE (SIMPLIFIED + STABLE)
    df2["score"] = (
        w_clap * df2["clap_sim"]
        + w_emo * df2["emotion_score"]
        + w_mod * df2["year_norm"]
        + w_energy_pref * (1 - abs(df2["energy"] - a))
    )

    # --------------------------------------------------
    # USER TASTE BIAS (gentle, additive)
    # --------------------------------------------------
    if user_taste:
        top_genres = set(user_taste.get("top_genres", []))

        if top_genres:
            genre_text = (
                df2["name"].str.lower()
                + " "
                + df2["artists"].astype(str).str.lower()
            )

            escaped_genres = [re.escape(g.lower()) for g in top_genres]

            taste_mask = genre_text.str.contains(
                "|".join(escaped_genres),
                na=False
            )

            # small but meaningful boost
            df2.loc[taste_mask, "score"] += 0.35

    # --------------------------------------------------
    # HARD OST / THEME PENALTY
    # --------------------------------------------------
    theme_terms = [
        "theme", "title theme", "main theme",
        "file select", "soundtrack", "ost",
        "from ", "opening", "ending"
    ]

    theme_text = (
        df2["name"].str.lower()
        + " "
        + df2["artists"].astype(str).str.lower()
    )

    is_theme = theme_text.str.contains(
        "|".join(theme_terms),
        na=False
    )

    df2.loc[is_theme, "score"] -= 0.6

    # penalize heavy instrumentals (but don't kill vocals)
    df2["score"] -= 0.35 * df2["instrumentalness"]




    # popularity bias
    df2["score"] += 0.15 * df2["pop_norm"]

    NEUTRAL_V = 0.5
    NEUTRAL_A = 0.5

    neutral_dist = np.sqrt(
        (df2["valence"] - NEUTRAL_V) ** 2 +
        (df2["energy"] - NEUTRAL_A) ** 2
    )
    df2["score"] += 0.35 * neutral_dist

    # INTENT SHAPING
    # shared shaping
    df2["score"] += cfg["energy_bias"] * df2["energy"]
    df2["score"] += cfg["vocal_boost"] * df2["speechiness"]
    df2["score"] -= cfg["instrumental_penalty"] * df2["instrumentalness"]

    # intent-specific constraints
    if intent == "warm_soft":
        # baby pink / tender warmth
        df2["score"] += 0.4 * df2["valence"]          # prefer positive emotion
        df2["score"] -= 0.4 * df2["energy"]           # avoid urgency
        df2["score"] -= 0.3 * (1 - df2["speechiness"])# avoid wordless music

    elif intent == "cool_soft":
        # lavender / calm distance
        df2["score"] -= 0.3 * df2["energy"]
        df2["score"] += 0.1 * (1 - df2["valence"])     # allow gentle melancholy

    elif intent == "dark_moody":
        # deep / introspective
        df2["score"] -= 0.2 * df2["energy"]
        df2["score"] += 0.3 * (1 - df2["valence"])     # sadness allowed

    # ROMANCE PRIOR (ONLY WHEN NEEDED)
    ROMANCE_TERMS = [
        "love", "kiss", "heart", "darling",
        "fall", "you", "us", "night", "baby"
    ]

    romance_mask = df2["name"].str.lower().str.contains(
        "|".join(ROMANCE_TERMS), na=False
    )

    if cfg.get("romance_bias", 0) > 0:
        df2.loc[romance_mask, "score"] += cfg["romance_bias"]

    # GAME OST REMOVAL
    GAME_FRANCHISES = [
        "pokemon", "pokémon", "zelda", "fire emblem",
        "final fantasy", "chrono", "kingdom hearts",
        "nintendo", "square enix", "capcom", "atlus"
    ]

    GAME_TERMS = [
        "title screen", "main menu", "overworld",
        "route", "battle", "boss", "stage", "level",
        "theme from", "video game", "game music",
        "game bgm", "game soundtrack", "from \""
    ]

    text_all = (
        df2["name"].str.lower() + " " +
        df2["artists"].astype(str).str.lower()
    )

    is_game_ost = (
        text_all.str.contains("|".join(GAME_FRANCHISES), na=False) |
        text_all.str.contains("|".join(GAME_TERMS), na=False)
    )

    is_allowed = text_all.str.contains("|".join(ALLOW_TERMS), na=False)

    df2 = df2[~(is_game_ost & ~is_allowed)]
    if user_profile["avoid_game_ost"]:
        df2 = df2[~is_game_ost]

    # CLASSICAL DETECTION 
    CLASSICAL_TERMS = [
        "bach", "chopin", "mozart", "beethoven",
        "prelude", "sonata", "symphony",
        "concerto", "op.", "opus", "movement"
    ]

    def classical_mask_fn(frame):
        return (
            frame["name"].str.lower().str.contains("|".join(CLASSICAL_TERMS), na=False)
            | frame["artists"].astype(str).str.lower().str.contains("|".join(CLASSICAL_TERMS), na=False)
        )

    # STABILITY + DEDUPLICATION
    df2 = df2.reset_index(drop=True)
    df2["score"] = df2["score"].clip(lower=0)

    df2["song_key"] = (
        df2["name"].str.lower().str.strip()
        + "___"
        + df2["artists"].astype(str).str.lower().str.strip()
    )

    df2 = df2.sort_values("score", ascending=False)
    df2 = df2.drop_duplicates("song_key", keep="first")

    df2["_artist_key"] = df2["artists"].astype(str)
    df2 = df2.groupby("_artist_key", as_index=False).head(2)

    classical_df = df2[classical_mask_fn(df2)].sort_values("score", ascending=False).head(2)
    non_classical_df = df2[~classical_mask_fn(df2)]
    df2 = pd.concat([non_classical_df, classical_df], ignore_index=True)

    df2 = df2.sample(frac=1, random_state=None)

    # FINAL RETURN
    top = df2.sort_values("score", ascending=False).head(limit * 2)

    seen = set()
    final = []

    for _, r in top.iterrows():
        key = r["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        final.append(r)
        if len(final) == limit:
            break

    return [
        {
            "id": r["id"],
            "name": r["name"],
            "artists": r["artists"],
            "album_image": None,
            "preview_url": None,
            "external_url": f"https://open.spotify.com/track/{r['id']}"
        }
        for r in final
    ]
