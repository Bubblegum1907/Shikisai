import numpy as np

# Fixed imports using relative paths
from .spotify_fetch import SpotifyFetcher
from .lyrics_embedder import LyricsEmbedder
from .clap_encoder import ClapEncoder
from dotenv import load_dotenv

load_dotenv()

def generate_vibe_vector(access_token, limit=20):
    sp_fetcher = SpotifyFetcher()
    sp = sp_fetcher._get_sp_client(access_token)
    
    clap = ClapEncoder()
    embedder = LyricsEmbedder(clap)
    
    print(f"Fetching top {limit} tracks...")
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range='medium_term')['items']
    
    embeddings = []
    
    for track in top_tracks:
        title = track['name']
        artist = track['artists'][0]['name']
        
        print(f"Processing: {title} by {artist}")
        
        vector = embedder.embed_song(title, artist)
        
        if vector is not None:
            embeddings.append(vector)
            
    if not embeddings:
        print("No embeddings generated.")
        return None
    
    # Linear decay weights (giving more importance to top-played tracks)
    weights = np.linspace(1.0, 0.5, num=len(embeddings))
    vibe_vector = np.average(embeddings, axis=0, weights=weights)
    vibe_vector = vibe_vector / (np.linalg.norm(vibe_vector) + 1e-9)
    print("Vibe Vector generated successfully.")
    
    return vibe_vector