import axios from "axios";

const BACKEND = import.meta.env.VITE_BACKEND_URL;

export async function exchangeSpotifyCode(code) {
  const res = await axios.post(`${BACKEND}/auth/spotify`, { code });
  return res.data;
}

export async function getPersonalizedRecs({ hex, mood, user_id }) {
  const res = await axios.post(`${BACKEND}/recommend_personalized`, {
    hex,
    mood,
    user_id
  });
  return res.data;
}
