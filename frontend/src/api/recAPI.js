export async function getRecs(color) {
  const token = localStorage.getItem("spotify_token");
  const refreshToken = localStorage.getItem("spotify_refresh_token");

  const res = await fetch(
    `/api/recommend?hex=${encodeURIComponent(color)}&k=10&token=${encodeURIComponent(token)}&refresh_token=${encodeURIComponent(refreshToken)}`
  );

  if (!res.ok) {
    throw new Error("Failed to fetch recommendations");
  }

  return await res.json();
}

