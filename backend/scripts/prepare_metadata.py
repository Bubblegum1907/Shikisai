import pandas as pd
import json
from pathlib import Path

# Setup paths
backend_root = Path(__file__).resolve().parent.parent
csv_path = backend_root / "data" / "my_tracks_with_clap.csv"
json_path = backend_root / "data" / "song_metadata.json"

print("🏗️ Building metadata from 5,639 tracks...")

# Read the recovered CSV
df = pd.read_csv(csv_path)

# Ensure columns exist for the AI to fill later
cols_to_add = ['clap_embed', 'valence', 'energy', 'instrumentalness', 'speechiness']
for col in cols_to_add:
    if col not in df.columns:
        df[col] = None

# Save to JSON for the frontend and the embedders
df.to_json(json_path, orient="records", indent=2)

print(f"✅ song_metadata.json created at {json_path}")
print("🚀 Now you can run your lyrics embedding script!")