/**
 * recAPI.js
 *
 * Fetches color-based music recommendations from the backend.
 *
 * FIX: Tokens are now sent in the Authorization header instead of
 * query params. Query param tokens get logged in server logs, browser
 * history, and any proxy sitting between client and server.
 */

export async function getRecs(color) {
  const token = localStorage.getItem("spotify_token");
  const refreshToken = localStorage.getItem("spotify_refresh_token");

  // Build headers — always send content type, conditionally send auth
  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (refreshToken) {
    headers["X-Refresh-Token"] = refreshToken;
  }

  const url = `/api/recommend?hex=${encodeURIComponent(color)}&k=10`;

  const res = await fetch(url, {
    method: "GET",
    headers,
  });

  if (res.status === 401) {
    // Token expired — clear storage and let the user reconnect
    localStorage.removeItem("spotify_token");
    localStorage.removeItem("spotify_refresh_token");
    localStorage.setItem("spotify_connected", "false");
    throw new Error("Spotify session expired. Please reconnect.");
  }

  if (!res.ok) {
    throw new Error(`Failed to fetch recommendations (${res.status})`);
  }

  return await res.json();
}