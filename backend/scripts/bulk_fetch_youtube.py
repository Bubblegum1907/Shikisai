import pandas as pd
import subprocess
import os
import time
from pathlib import Path

FFMPEG_BIN_PATH = r"C:\Users\Iba shibli\Downloads\ffmpeg-2026-04-01-git-eedf8f0165-essentials_build\ffmpeg-2026-04-01-git-eedf8f0165-essentials_build\bin" 

backend_root = Path(__file__).resolve().parent.parent
csv_path = backend_root / "data" / "my_tracks_with_clap.csv"
audio_dir = backend_root / "data" / "songs"
audio_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(csv_path)

success_count = 0
fail_count = 0

for index, row in df.iterrows():
    track_id = row['id']
    file_path = audio_dir / f"{track_id}.mp3"
    
    if file_path.exists():
        continue

    query = f"ytsearch1:{row['artists']} {row['name']} audio"
    
    try:
        subprocess.run([
            "yt-dlp",
            "--ffmpeg-location", FFMPEG_BIN_PATH,
            "-x", 
            "--audio-format", "mp3",
            "--postprocessor-args", "ffmpeg:-ss 00:00:45 -t 00:00:30", 
            "--output", f"{audio_dir}/{track_id}.%(ext)s",
            query
        ], check=True)
        
        success_count += 1
        print(f"[{index}/{len(df)}] Downloaded: {row['name']}")
        
    except Exception as e:
        fail_count += 1
        print(f"[{index}/{len(df)}] Failed: {row['name']}")
        print(f"ERROR DETAIL: {e}") 
        continue 

print("\nFINISHED")
print(f"Successfully fetched: {success_count}")
print(f"Failed: {fail_count}")