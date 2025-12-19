# Shikisai: Color-Based Music Recommendation System

Shikisai is a full-stack, AI-driven music recommendation system that maps **colors to emotions** and recommends songs that match both the **emotional tone of a selected color** and the **listener’s personal music taste**.

The system combines color psychology, audio embeddings, and Spotify user data to generate emotionally coherent and personalized playlists.

---

## Features

- Color → emotion mapping using color psychology
- Emotion-aware music recommendation
- Personalization via Spotify listening history
- CLAP embeddings for semantic audio–text alignment
- FAISS-based similarity search for scalable retrieval
- Full-stack implementation (FastAPI backend + React frontend)

---

## System Overview

1. **User selects a color** from the UI
2. Color is mapped to an **emotion and mood description**
3. The mood text is embedded using **CLAP**
4. Songs are ranked using a hybrid score combining:
   - CLAP similarity
   - Emotional distance (valence & arousal)
   - Audio features (energy, valence, popularity, recency)
   - User taste profile (derived from Spotify history)
5. Final recommendations are returned and displayed

---

## Personalization

When connected to Spotify, Shikisai builds a lightweight **user taste profile** from the user’s top tracks, including:

- Dominant genres
- Preference for softer vs energetic music
- Pop vs non-pop bias

This profile is applied as a **gentle bias** during ranking, ensuring recommendations remain mood-faithful while still reflecting personal taste.

---

## Tech Stack

### Backend
- Python
- FastAPI
- FAISS (vector similarity search)
- CLAP (Contrastive Language–Audio Pretraining)
- Spotipy (Spotify Web API)
- NumPy, Pandas, Scikit-learn

### Frontend
- React
- Vite
- Tailwind CSS

---

## Setup Instructions

### Backend
cd backend  
python -m venv clapenv  
clapenv\Scripts\activate  
pip install -r requirements.txt  
uvicorn app.main:app --reload  

### Frontend
cd frontend  
npm install  
npm run dev  

### Spotify Authentication
To enable personalization, create a Spotify Developer app and set the following environment variables:  
SPOTIFY_CLIENT_ID  
SPOTIFY_CLIENT_SECRET  
SPOTIFY_REDIRECT_URI  

### Current Status
Core recommendation system implemented  
Spotify personalization integrated  
FAISS index built from Spotify data  
UI functional with color-based interaction  

### Future improvements may include:
Playlist creation on Spotify  
Improved genre-aware embedding  
Model fine-tuning for emotional alignment  

### Motivation
Shikisai explores how abstract visual input (color) can be translated into emotional and musical experiences, blending human perception with machine learning.  
This project was built as a learning-driven system combining AI, recommendation systems, and full-stack development.  

### Author
Iba Shibli  
