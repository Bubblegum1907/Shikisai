import os
import math
import traceback
import numpy as np
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Internal Utils
from .utils.clap_encoder import ClapEncoder
from .utils.spotify_auth import SpotifyAuth
from .utils.spotify_fetch import SpotifyFetcher
from .utils.palette_utils import load_palette 
from .utils.color_utils import hex_to_lab
from .utils.local_recommender import recommend_hybrid
from .models.song_store import SongStore

app = FastAPI(title="Shikisai Recommender")

# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SINGLETONS ---
clap = ClapEncoder()
spotify_auth = SpotifyAuth()
spotify_fetcher = SpotifyFetcher()
store = SongStore(clap=clap)
COLOR_PALETTE = load_palette()

@app.on_event("startup")
def startup_event():
    try:
        store.load_index()
        print(f"✅ FAISS index loaded. Ready to search {len(COLOR_PALETTE)} colors.")
    except Exception as e:
        print("⚠️ No FAISS index found — will build on demand.", e)

# --- HELPER: COLOR MAPPING ---
def get_color_metadata(hex_code: str):
    """Maps a hex code to emotional prompts and VAD values using Perceptual Matching."""
    user_hex = hex_code.strip().upper().lstrip('#')
    
    # 1. Exact Match Check
    match = next((c for c in COLOR_PALETTE 
                  if str(c.get('hex', '')).strip().lstrip('#').upper() == user_hex), None)
    
    # 2. Perceptual Nearest Neighbor Fallback
    if not match:
        try:
            user_lab = hex_to_lab(hex_code)
            def calculate_distance(color_obj):
                l_diff = user_lab[0] - color_obj['lab'][0]
                a_diff = user_lab[1] - color_obj['lab'][1]
                b_diff = user_lab[2] - color_obj['lab'][2]
                return math.sqrt(l_diff**2 + a_diff**2 + b_diff**2)
            
            match = min(COLOR_PALETTE, key=calculate_distance)
        except Exception:
            return "Atmospheric and balanced music.", (0.5, 0.5)

    e1, e2 = match['emotion1'], match['emotion2']
    v, a = match['vad']['valence'], match['vad']['arousal']
    
    prompt = (f"A professional audio recording featuring instrumentation that is {e1} and {e2}. "
              f"The sonic texture evokes {e2}. Tailored for the visual frequency of #{user_hex}.")
    
    return prompt, (v, a)

# --- BACKGROUND TASKS ---
def perform_indexing(payload, fetcher, song_store):
    try:
        print(f"🚀 Background Indexing: Fetching tracks for token {payload.token[:10]}...")
        tracks = fetcher.fetch_tracks_from_user(
            access_token=payload.token,
            fetch_playlists=payload.fetch_playlists,
            fetch_saved=payload.fetch_saved,
            fetch_top=payload.fetch_top,
            max_per_source=payload.max_tracks_per_source
        )
        
        if tracks:
            n_added = song_store.add_spotify_tracks(tracks)
            print(f"✅ Success! Indexed {n_added} user tracks into FAISS.")
        else:
            print("⚠️ No tracks found for this user.")
            
    except Exception as e:
        print(f"❌ Background Indexing Failed: {str(e)}")
        traceback.print_exc()

# --- API ENDPOINTS ---
@app.get("/auth/login")
def auth_login():
    return RedirectResponse(spotify_auth.get_authorize_url())

@app.get("/auth/callback")
def auth_callback(code: str | None = None):
    if not code: raise HTTPException(400, "Missing OAuth code")
    try:
        # Crucial: This swaps the code for real tokens
        token_info = spotify_auth.oauth.get_access_token(code)
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")
        
        # Redirect back to the FRONTEND with the tokens
        return RedirectResponse(
            url=f"http://127.0.0.1:8080/callback?token={access_token}&refresh_token={refresh_token}"
        )
    except Exception as e:
        raise HTTPException(400, f"Token exchange failed: {str(e)}")

class BuildSpotifyPayload(BaseModel):
    token: str
    fetch_playlists: bool = True
    fetch_saved: bool = True
    fetch_top: bool = True
    max_tracks_per_source: int = 500

@app.post("/build_index_spotify")
def build_index_spotify(payload: BuildSpotifyPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(perform_indexing, payload, spotify_fetcher, store)
    return {"status": "accepted", "message": "Taste indexing started."}

@app.get("/recommend")
def recommend(hex: Optional[str] = None, k: int = 10, token: Optional[str] = None, refresh_token: Optional[str] = None):
    try:
        if not hex: return {"ok": True}

        # 1. Map Hex to Context
        prompt, (v, a) = get_color_metadata(hex)

        # 2. Taste Profile
        taste = None
        if token:
            try:
                taste = spotify_fetcher.get_user_taste_profile(token, refresh_token)
            except Exception as e:
                print(f"⚠️ Taste fetch failed: {e}")

        # 3. Vector Generation (Ensuring 512-dim match for FAISS)
        text_emb = clap.encode_text(prompt)
        text_emb = np.asarray(text_emb, dtype=np.float32).flatten()
        
        if text_emb.size > 512:
            text_emb = text_emb[:512]
        else:
            text_emb = np.pad(text_emb, (0, max(0, 512 - text_emb.size)))

        # 4. Hybrid Retrieval
        recs = recommend_hybrid(
            query_embed=text_emb,
            v=v, a=a,
            hex_color=hex,
            limit=k,
            user_taste=taste,
            store=store 
        )

        return {
            "hex": hex,
            "prompt": prompt,
            "vad": {"valence": round(v, 2), "arousal": round(a, 2)},
            "recommendations": recs,
            "personalized": taste is not None
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))