export async function getRecs(color) {
  const token = localStorage.getItem("spotify_token");
  const refreshToken = localStorage.getItem("spotify_refresh_token");

  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (refreshToken) {
    headers["X-Refresh-Token"] = refreshToken;
  }

  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

  const baseUrl = backendBaseUrl.rstrip ? backendBaseUrl.rstrip("/") : backendBaseUrl.replace(/\/$/, "");
  
  const url = `${baseUrl}/recommend?hex=${encodeURIComponent(color)}&k=10`;

  const res = await fetch(url, {
    method: "GET",
    headers,
  });

  if (res.status === 401) {
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