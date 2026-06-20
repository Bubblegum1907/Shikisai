import pandas as pd
import json
import librosa
import numpy as np
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
csv_path = backend_root / "data" / "my_tracks_with_clap.csv"
json_path = backend_root / "data" / "song_metadata.json"
audio_dir = backend_root / "data" / "songs"

def analyze_audio_vibe(track_id):
    file_path = audio_dir / f"{track_id}.mp3"
    if not file_path.exists(): return None, None
    
    try:
        y, sr = librosa.load(str(file_path), duration=30)
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        brightness = np.mean(spectral_centroids)
        
        rms = librosa.feature.rms(y=y)
        db_rms = librosa.amplitude_to_db(rms, ref=np.max) 
        avg_db = np.mean(db_rms) 
        
        norm_loudness = np.clip((avg_db + 40) / 40, 0, 1) 
        norm_brightness = np.clip(brightness / 5000, 0, 1)
        
        final_energy = (norm_loudness * 0.4) + (norm_brightness * 0.6)

        y_harm, y_perc = librosa.effects.hpss(y)
        instrum = 1.0 - (np.sum(np.abs(y_harm)) / (np.sum(np.abs(y)) + 1e-6))

        return float(np.clip(final_energy, 0.1, 0.9)), float(np.clip(instrum, 0.0, 1.0))

    except Exception as e:
        print(f"Error analyzing {track_id}: {e}")
        return 0.5, 0.5

def update_metadata():
    # 1. Load the existing JSON as the primary DataFrame
    # This ensures all your lyrics and previous work are preserved
    if not json_path.exists():
        print("Metadata JSON not found! Please ensure it's in backend/data/")
        return

    print(f"🔄 Loading existing metadata from {json_path}...")
    df = pd.read_json(json_path)
    df['id'] = df['id'].astype(str)
    
    # Ensure our target columns exist so we can check them
    for col in ['energy', 'instrumentalness', 'preview_url']:
        if col not in df.columns:
            df[col] = np.nan

    # 2. Count how many we actually need to process
    to_process = df[df['energy'].isna() | df['preview_url'].isna()]
    print(f"Total tracks in JSON: {len(df)}")
    print(f"Tracks needing analysis: {len(to_process)}")

    if len(to_process) == 0:
        print("✨ Everything looks up to date!")
        return

    # 3. Process only the missing ones
    for index, row in df.iterrows():
        # Skip if already done
        if pd.notna(row.get('energy')) and pd.notna(row.get('preview_url')):
            continue

        track_id = str(row['id'])
        file_path = audio_dir / f"{track_id}.mp3"
        
        if file_path.exists():
            eng, ins = analyze_audio_vibe(track_id)
            
            if eng is not None:
                df.at[index, 'energy'] = eng
                df.at[index, 'instrumentalness'] = ins
                df.at[index, 'preview_url'] = f"/data/songs/{track_id}.mp3"
                print(f"[{index}] Analyzed: {row.get('name', track_id)} (Eng: {eng:.2f})")
        else:
            # If no file, set a neutral default so we don't keep trying forever
            if pd.isna(df.at[index, 'energy']):
                df.at[index, 'energy'] = 0.5
                df.at[index, 'instrumentalness'] = 0.5

        # Save checkpoint every 10 tracks to be safe
        if index % 10 == 0:
            df.to_json(json_path, orient="records", indent=2)

    # Final Save
    df.to_json(json_path, orient="records", indent=2)
    print(f"\n✨ Success! Audio features merged into your metadata.")

if __name__ == "__main__":
    update_metadata()