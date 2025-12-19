import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy

load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8080/callback")
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

class SpotifyAuth:
    def __init__(self):
        if CLIENT_ID is None or CLIENT_SECRET is None:
            raise RuntimeError("Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in .env")
        
        self.oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=".spotifycache"
        )

    def get_authorize_url(self):
        return self.oauth.get_authorize_url()

    def exchange_code_for_token(self, code):
        token_info = self.oauth.get_access_token(code)
        return token_info

    def get_spotify_client(self, access_token: str):
        return spotipy.Spotify(auth=access_token)
