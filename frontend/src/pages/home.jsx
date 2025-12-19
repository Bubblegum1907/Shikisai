import { useEffect, useState } from "react";
import LoginButton from "../components/LoginButton";
import ColorWheel from "../components/colorwheel";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const isConnected =
      localStorage.getItem("spotify_connected") === "true";
    setConnected(isConnected);
  }, []);

  const handlePick = (hex) => {
    navigate(`/recommendations?color=${encodeURIComponent(hex)}`);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: "32px",
        padding: "40px 20px",
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: 600 }}>
        Shikisai
      </h1>

      {/* Spotify login / status */}
      {!connected ? (
        <LoginButton />
      ) : (
        <div
          style={{
            padding: "10px 22px",
            borderRadius: "999px",
            background: "#E8F9EF",
            color: "#2F855A",
            fontWeight: 600,
          }}
        >
          ✓ Connected to Spotify
        </div>
      )}

      {/* Color wheel */}
      <ColorWheel size={420} onPick={handlePick} />
    </div>
  );
}
