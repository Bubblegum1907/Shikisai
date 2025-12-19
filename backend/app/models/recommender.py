# backend/app/models/recommender.py
"""
Light adapter to use the new local_recommender.recommend_hybrid
as the project's recommender. This replaces the FAISS SongStore path.
"""

from typing import List, Dict, Optional

# Import the hybrid recommender you already installed (the fixed version)
# Use absolute import so it works when running uvicorn from project root.
from app.utils.local_recommender import recommend_hybrid

class Recommender:
    def __init__(self):
        # Nothing to initialize for now; recommend_hybrid uses module-level data.
        pass

    def recommend(
        self,
        query_embed,          # CLAP vector (list/np.array)
        valence: float,       # target valence
        arousal: float,       # target arousal (energy)
        k: int = 10,
        preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Returns a list of recommendation dicts in a simple consistent shape.
        The shape is similar to what your frontend expects; adjust if needed.
        """
        # call the cleaned recommender
        results = recommend_hybrid(query_embed=query_embed, v=valence, a=arousal, preferences=preferences, limit=k)

        # Map results (from recommend_hybrid) to a consistent API response shape.
        # recommend_hybrid returns items with keys: id, name, artists, external_url, ...
        mapped = []
        for idx, r in enumerate(results):
            mapped.append({
                "title": r.get("name"),
                "local_path": None,
                "spotify_id": r.get("id"),
                "artists": r.get("artists"),
                "genres": r.get("genres", []),   # may be missing; keep empty list if so
                "source": "local",
                "score": r.get("score", None),   # recommend_hybrid doesn't currently return score; None is fine
                "idx": idx
            })
        return mapped
