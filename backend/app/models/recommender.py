"""
Light adapter to use the new local_recommender.recommend_hybrid
as the project's recommender. This replaces the FAISS SongStore path.
"""

from typing import List, Dict, Optional
from app.utils.local_recommender import recommend_hybrid

class Recommender:
    def __init__(self):
        pass

    def recommend(
        self,
        query_embed,          # CLAP vector
        valence: float,       # target valence
        arousal: float,       # target arousal
        k: int = 10,
        preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Returns a list of recommendation dicts in a simple consistent shape.
        The shape is similar to what your frontend expects; adjust if needed.
        """
        results = recommend_hybrid(query_embed=query_embed, v=valence, a=arousal, preferences=preferences, limit=k)

        # recommend_hybrid returns items with keys: id, name, artists, external_url, ...
        mapped = []
        for idx, r in enumerate(results):
            mapped.append({
                "title": r.get("name"),
                "local_path": None,
                "spotify_id": r.get("id"),
                "artists": r.get("artists"),
                "genres": r.get("genres", []), 
                "source": "local",
                "score": r.get("score", None), 
                "idx": idx
            })
        return mapped
