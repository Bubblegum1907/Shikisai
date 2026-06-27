import os
import math
import traceback
import numpy as np
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from .utils.clap_encoder import ClapEncoder
from .utils.spotify_auth import SpotifyAuth
from .utils.spotify_fetch import SpotifyFetcher
from .utils.palette_utils import load_palette
from .utils.color_utils import hex_to_lab
from .utils.local_recommender import recommend_hybrid
from .utils.taste_profiler import generate_vibe_vector
from .models.song_store import SongStore

app = FastAPI(title="Shikisai Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# App-level singletons
# ---------------------------------------------------------------------------
clap = ClapEncoder()
spotify_auth = SpotifyAuth()
spotify_fetcher = SpotifyFetcher()
store = SongStore(clap=clap)
COLOR_PALETTE = load_palette()
VIBE_CACHE: dict = {}

# Tracks background indexing state so the frontend can poll for readiness
indexing_status: dict = {
    "running": False,
    "done": False,
    "tracks_indexed": 0,
    "error": None,
}


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    try:
        store.load_index()
        print("[Startup] FAISS index loaded successfully.")
    except Exception as e:
        print("[Startup] No FAISS index found — will build on demand.", e)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_token(request: Request) -> Optional[str]:
    """
    Reads the Spotify access token from the Authorization header.
    Expected format: 'Bearer <token>'
    Falls back to None if missing or malformed.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):].strip()
        return token if token else None
    return None


def _extract_refresh_token(request: Request) -> Optional[str]:
    """Reads the refresh token from the custom X-Refresh-Token header."""
    token = request.headers.get("X-Refresh-Token", "").strip()
    return token if token else None


def get_color_metadata(hex_code: str):
    """
    Maps a hex code to emotional prompts and VAD values using
    perceptual (CIELAB) nearest-neighbour matching.
    """
    user_hex = hex_code.strip().upper().lstrip("#")

    match = next(
        (c for c in COLOR_PALETTE
         if str(c.get("hex", "")).strip().lstrip("#").upper() == user_hex),
        None,
    )

    if not match:
        try:
            user_lab = hex_to_lab(hex_code)

            def lab_distance(color_obj):
                l, a, b = user_lab
                cl, ca, cb = color_obj["lab"]
                return math.sqrt((l - cl) ** 2 + (a - ca) ** 2 + (b - cb) ** 2)

            match = min(COLOR_PALETTE, key=lab_distance)
            print(
                f"[Color Match] #{user_hex} matched perceptually to "
                f"{match.get('hex')}"
            )
        except Exception as e:
            print(f"[Color Match Error] #{hex_code}: {e}")
            return "Atmospheric and balanced music.", (0.5, 0.5)

    e1, e2 = match["emotion1"], match["emotion2"]
    v, a = match["vad"]["valence"], match["vad"]["arousal"]

    prompt = (
        f"A professional audio recording featuring instrumentation that is "
        f"{e1} and {e2}. The sonic texture evokes {e2}. "
        f"Tailored for the visual frequency of #{user_hex}."
    )

    return prompt, (v, a)


def _run_indexing(token: str, payload, fetcher, song_store):
    """Background task: fetch user tracks and add them to the FAISS store."""
    global indexing_status
    indexing_status["running"] = True
    indexing_status["done"] = False
    indexing_status["error"] = None
    indexing_status["tracks_indexed"] = 0

    try:
        print(f"[Indexing] Starting for token …{token[-6:]}")
        tracks = fetcher.fetch_tracks_from_user(
            access_token=token,
            fetch_playlists=payload.fetch_playlists,
            fetch_saved=payload.fetch_saved,
            fetch_top=payload.fetch_top,
            max_per_source=payload.max_tracks_per_source,
        )

        if tracks:
            n_added = song_store.add_spotify_tracks(tracks)
            indexing_status["tracks_indexed"] = n_added
            print(f"[Indexing] Loaded {n_added} unique tracks.")
        else:
            print("[Indexing] No tracks found for this user.")

    except Exception as e:
        indexing_status["error"] = str(e)
        print(f"[Indexing Failed] {e}")
        traceback.print_exc()
    finally:
        indexing_status["running"] = False
        indexing_status["done"] = True


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.get("/auth/login")
def auth_login():
    return RedirectResponse(spotify_auth.get_authorize_url())


@app.get("/auth/callback")
def auth_callback(code: Optional[str] = None):
    if not code:
        raise HTTPException(400, "Missing OAuth code")
    try:
        token_info = spotify_auth.oauth.get_access_token(code)
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")
        return RedirectResponse(
            url=(
                f"http://127.0.0.1:8080/callback"
                f"?token={access_token}"
                f"&refresh_token={refresh_token}"
            )
        )
    except Exception as e:
        raise HTTPException(400, f"Token exchange failed: {e}")


# ---------------------------------------------------------------------------
# Indexing routes
# ---------------------------------------------------------------------------
class BuildSpotifyPayload(BaseModel):
    fetch_playlists: bool = True
    fetch_saved: bool = True
    fetch_top: bool = True
    max_tracks_per_source: int = 500


@app.post("/build_index_spotify")
def build_index_spotify(
    payload: BuildSpotifyPayload,
    background_tasks: BackgroundTasks,
    request: Request,
):
    token = _extract_token(request)
    if not token:
        raise HTTPException(401, "Missing Authorization header")

    if indexing_status["running"]:
        return {"status": "already_running", "message": "Indexing already in progress."}

    background_tasks.add_task(_run_indexing, token, payload, spotify_fetcher, store)
    return {"status": "accepted", "message": "Taste indexing started."}


@app.get("/indexing_status")
def get_indexing_status():
    """
    Poll this endpoint to check whether background track indexing has finished.
    The frontend can use this to show a loading state after connecting Spotify.
    """
    return {
        "running": indexing_status["running"],
        "done": indexing_status["done"],
        "tracks_indexed": indexing_status["tracks_indexed"],
        "error": indexing_status["error"],
        "store_size": len(store.metadata) if store.metadata else 0,
    }

def sanitize_data(data):
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(x) for x in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None  # Replaces NaN/Inf with JSON-compliant null
    return data

# ---------------------------------------------------------------------------
# Recommendation route
# ---------------------------------------------------------------------------
@app.get("/recommend")
def recommend(
    request: Request,
    hex: Optional[str] = None,
    k: int = 10,
):
    """
    Returns color-based music recommendations.

    Auth: pass Spotify token as  'Authorization: Bearer <token>'
          and refresh token as   'X-Refresh-Token: <refresh_token>'
    """
    try:
        print(f"\n[RECOMMEND] hex={hex}, k={k}")

        if not hex:
            return {
                "hex": None,
                "prompt": "",
                "vad": {"valence": 0.5, "arousal": 0.5},
                "recommendations": [],
                "personalized": False,
                "warning": "No hex code provided",
            }

        # 1. Color → emotional prompt + VAD
        prompt, (v, a) = get_color_metadata(hex)
        print(f"[RECOMMEND] prompt='{prompt}' VAD=({v}, {a})")

        # 2. Optional personalisation — token now comes from header
        token = _extract_token(request)
        vibe_vec = None

        if token:
            if token in VIBE_CACHE:
                vibe_vec = VIBE_CACHE[token]
                print("[RECOMMEND] Vibe vector from cache.")
            else:
                try:
                    vibe_vec = generate_vibe_vector(token)
                    VIBE_CACHE[token] = vibe_vec
                    print("[RECOMMEND] Vibe vector generated.")
                except Exception as e:
                    print(f"[RECOMMEND] Vibe profiling failed (non-fatal): {e}")

        # 3. Encode the color prompt with CLAP
        print("[RECOMMEND] Encoding prompt with CLAP…")
        text_emb = clap.encode_text(prompt)
        text_emb = np.asarray(text_emb, dtype=np.float32).flatten()

        if text_emb.size > 512:
            text_emb = text_emb[:512]
        else:
            text_emb = np.pad(text_emb, (0, max(0, 512 - text_emb.size)))

        # 4. Hybrid recommendation
        print("[RECOMMEND] Querying hybrid pool…")
        recs = recommend_hybrid(
            query_embed=text_emb,
            v=v,
            a=a,
            hex_color=hex,
            limit=k,
            vibe_vector=vibe_vec,
            store=store,
        )

        if recs is None:
            recs = []

        print(f"[RECOMMEND] Returning {len(recs)} tracks.")
        
        # --- SANITIZATION HAPPENS HERE ---
        response_data = {
            "hex": hex,
            "prompt": prompt,
            "vad": {"valence": round(v, 2), "arousal": round(a, 2)},
            "recommendations": recs,
            "personalized": vibe_vec is not None,
        }
        
        return sanitize_data(response_data)

    except Exception as e:
        print("[RECOMMEND] Critical error:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))