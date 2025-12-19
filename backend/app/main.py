print("### FASTAPI APP WITH CORS IS RUNNING ###")

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from urllib.parse import urlencode

import os
import traceback
import numpy as np

from app.utils.clap_encoder import ClapEncoder
from app.utils.color_to_text import color_to_text_prompt
from app.utils.spotify_auth import SpotifyAuth
from app.utils.spotify_fetch import SpotifyFetcher
from app.models.song_store import SongStore
from app.utils.local_recommender import recommend_hybrid

USER_TASTE = {}

# -----------------------------------------------------
# Load .env
# -----------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")

print("Loading .env from:", ENV_PATH)
load_dotenv(dotenv_path=ENV_PATH)

# -----------------------------------------------------
# App + Singletons
# -----------------------------------------------------
app = FastAPI(title="Shikisai Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # IMPORTANT: allows OPTIONS, POST, etc.
    allow_headers=["*"],
    expose_headers=["*"],
)

clap = ClapEncoder()
spotify_auth = SpotifyAuth()
spotify_fetcher = SpotifyFetcher()

store = SongStore(clap=clap)

# -----------------------------------------------------
# Startup
# -----------------------------------------------------
@app.on_event("startup")
def startup_event():
    try:
        store.load_index()
        print("FAISS index loaded successfully.")
    except Exception as e:
        print("No FAISS index found — will build on demand.", e)

# -----------------------------------------------------
# Spotify OAuth
# -----------------------------------------------------
@app.get("/auth/login")
def auth_login():
    url = spotify_auth.get_authorize_url()
    return RedirectResponse(url)


@app.get("/auth/callback")
def auth_callback(code: str | None = None):
    if not code:
        raise HTTPException(400, "Missing OAuth code")

    token_info = spotify_auth.exchange_code_for_token(code)

    return RedirectResponse(
        url=f"http://127.0.0.1:8080/callback?token={token_info['access_token']}"
    )


# -----------------------------------------------------
# Build Index from Spotify
# -----------------------------------------------------
class BuildSpotifyPayload(BaseModel):
    token: str
    fetch_playlists: bool = True
    fetch_saved: bool = True
    fetch_top: bool = True
    max_tracks_per_source: int = 500


@app.post("/build_index_spotify")
def build_index_spotify(payload: BuildSpotifyPayload):
    try:
        tracks = spotify_fetcher.fetch_tracks_from_user(
            access_token=payload.token,
            fetch_playlists=payload.fetch_playlists,
            fetch_saved=payload.fetch_saved,
            fetch_top=payload.fetch_top,
            max_per_source=payload.max_tracks_per_source,
        )
        print("FETCHED TRACK COUNT:", len(tracks))

        n_added = store.add_spotify_tracks(tracks)

        print(f"Indexed {n_added} tracks into FAISS.")

        return {"status": "ok", "n_added": n_added}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))

@app.options("/recommend")
def recommend_options():
    return {}

# -----------------------------------------------------
# Recommend Endpoint (1027-D)
# -----------------------------------------------------

@app.get("/recommend")
def recommend(hex: Optional[str] = None, k: int = 10, token: Optional[str] = None):
    try:
        # ----------------------------
        # Handle preflight / empty call
        # ----------------------------
        if not hex:
            return {"ok": True}

        # ----------------------------
        # Normalize hex
        # ----------------------------
        hex_color = hex.strip()

        # ----------------------------
        # Color → prompt + VAD
        # ----------------------------
        prompt, vad_vals = color_to_text_prompt(hex_color)
        print("PROMPT:", prompt)

        if vad_vals is not None and len(vad_vals) == 2:
            v, a = vad_vals
        else:
            v, a = 0.5, 0.5

        # ----------------------------
        # Encode prompt → CLAP
        # ----------------------------
        text_emb = clap.encode_text(prompt)
        text_emb = np.asarray(text_emb, dtype=np.float32)

        if text_emb.size >= 512:
            text_emb = text_emb[:512]
        else:
            pad = np.zeros(512 - text_emb.size, dtype=np.float32)
            text_emb = np.concatenate([text_emb, pad])

        # ----------------------------
        # Build 1027-D vector
        # ----------------------------
        audio_emb = np.zeros(512, dtype=np.float32)
        vad_emb = np.zeros(3, dtype=np.float32)

        query_vec = np.concatenate(
            [text_emb, audio_emb, vad_emb]
        ).astype("float32")

        _ = store.search(query_vec, k=200)

        taste = None
        if token:
            try:
                tracks = spotify_fetcher.fetch_tracks_from_user(
                    access_token=token,
                    fetch_playlists=False,
                    fetch_saved=False,
                    fetch_top=True,
                    max_per_source=30
                )
                taste = spotify_fetcher.build_taste_from_tracks(tracks)
            except Exception as e:
                print("Taste rebuild failed:", e)

        print("RECOMMEND TOKEN:", token)
        print("USING TASTE:", taste)

        recs = recommend_hybrid(
            query_embed=text_emb[:512],
            v=v,
            a=a,
            hex_color=hex_color,
            limit=k,
            user_taste=taste
        )

        return {
            "hex": hex_color,
            "prompt": prompt,
            "vad": {"valence": v, "arousal": a},
            "recommendations": recs
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {str(e)}"
        )