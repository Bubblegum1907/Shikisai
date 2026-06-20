import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "my_tracks_with_clap.csv"
ENV_PATH = ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)
API_KEY = os.getenv("LASTFM_API_KEY")

def get_lastfm_tags(artist, track):
    """Fetches top 5 tags for a track from Last.fm."""
    if not API_KEY:
        return "ERROR_NO_KEY"
        
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "track.getTopTags",
        "artist": artist,
        "track": track,
        "api_key": API_KEY,
        "format": "json"
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            tags = data.get('toptags', {}).get('tag', [])
            return ", ".join([t['name'] for t in tags[:5]])
    except Exception:
        return ""
    return ""

def enrich_data():
    if not CSV_PATH.exists():
        print(f"CSV not found at {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    
    if 'tags' not in df.columns:
        df['tags'] = ""
    
    df['tags'] = df['tags'].fillna("")

    todo_indices = df[df['tags'] == ""].index.tolist()
    
    if not todo_indices:
        print("All tracks already have tags.")
        return

    print(f"Hyper-Threaded Enrichment ({len(todo_indices)} remaining)")

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {
            executor.submit(get_lastfm_tags, df.at[i, 'artists'], df.at[i, 'name']): i 
            for i in todo_indices
        }
        
        for count, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Tagging")):
            idx = futures[future]
            try:
                df.at[idx, 'tags'] = future.result()
            except Exception as e:
                print(f"\nError at index {idx}: {e}")
            
            if count > 0 and count % 100 == 0:
                df.to_csv(CSV_PATH, index=False)

    df.to_csv(CSV_PATH, index=False)
    print(f"Enrichment Complete. CSV saved to {CSV_PATH}")

if __name__ == "__main__":
    enrich_data()