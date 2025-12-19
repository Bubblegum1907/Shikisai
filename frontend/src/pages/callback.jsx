import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Callback() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (!token) {
      console.error("No token received");
      navigate("/");
      return;
    }

    localStorage.setItem("spotify_token", token);
    localStorage.setItem("spotify_connected", "true");

    navigate("/");
  }, []);

  return (
    <div style={{ padding: 40 }}>
      <h2>Connecting to Spotify…</h2>
    </div>
  );
}
