import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

const BACKEND = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:7860";

async function triggerIndexing(token) {
  try {
    await fetch(`${BACKEND}/build_index_spotify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        fetch_playlists: true,
        fetch_saved: true,
        fetch_top: true,
        max_tracks_per_source: 500,
      }),
    });
    console.log("[Shikisai] Background indexing started.");
  } catch (err) {
    // Non-fatal — recommendations will still work without personalisation
    console.warn("[Shikisai] Could not start indexing:", err);
  }
}

export default function SpotifyAuthButton() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const connected = localStorage.getItem("spotify_connected") === "true";
    setIsConnected(connected);

    // If we just came back from OAuth with a fresh token, kick off indexing
    const token = localStorage.getItem("spotify_token");
    const alreadyIndexed = localStorage.getItem("indexing_triggered") === "true";

    if (connected && token && !alreadyIndexed) {
      triggerIndexing(token).then(() => {
        localStorage.setItem("indexing_triggered", "true");
      });
    }
  }, []);

  const handleConnect = () => {
    setIsLoading(true);
    // Small delay so the loading state renders before the browser navigates
    setTimeout(() => {
      window.location.href = `${BACKEND}/auth/login`;
    }, 80);
  };

  const handleDisconnect = () => {
    localStorage.removeItem("spotify_token");
    localStorage.removeItem("spotify_refresh_token");
    localStorage.removeItem("indexing_triggered");
    localStorage.setItem("spotify_connected", "false");
    setIsConnected(false);
    window.location.href = "/";
  };

  // -------------------------------------------------------------------------
  // Derived style values
  // -------------------------------------------------------------------------
  const buttonStyle = {
    position: "relative",
    padding: "14px 32px",
    borderRadius: "999px",
    fontSize: "0.95rem",
    fontWeight: 600,
    cursor: isLoading ? "wait" : "pointer",
    backdropFilter: "blur(12px) saturate(150%)",
    transition: "all 0.3s ease",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    opacity: isLoading ? 0.7 : 1,

    ...(isConnected
      ? {
          background: "rgba(239,68,68,0.15)",
          color: "#F87171",
          border: "1px solid rgba(239,68,68,0.3)",
          boxShadow: "0 10px 25px -5px rgba(239,68,68,0.2)",
        }
      : {
          background: "rgba(124,58,237,0.25)",
          color: "#FFFFFF",
          border: "1px solid rgba(255,255,255,0.3)",
          boxShadow: "0 10px 25px -5px rgba(124,58,237,0.4)",
        }),
  };

  // -------------------------------------------------------------------------
  // Icons
  // -------------------------------------------------------------------------
  const SpotifyIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.508 17.302c-.218.358-.683.472-1.042.254-2.812-1.718-6.353-2.106-10.518-1.157-.409.094-.818-.163-.912-.572-.094-.409.163-.818.572-.912 4.582-1.048 8.491-.597 11.646 1.33.359.219.473.684.254 1.041zm1.468-3.258c-.274.444-.852.585-1.296.311-3.218-1.977-8.125-2.551-11.93-1.397-.502.152-1.03-.135-1.182-.637-.152-.502.135-1.03.637-1.182 4.344-1.317 9.757-.674 13.46 1.601.444.274.585.852.311 1.296zm.128-3.395c-.33.539-1.033.709-1.572.38-3.824-2.272-10.126-2.481-13.784-1.371-.62.188-1.269-.168-1.457-.788-.188-.62.168-1.269.788-1.457 4.312-1.308 11.272-1.064 15.651 1.537.536.318.706 1.021.38 1.56z" />
    </svg>
  );

  const LogoutIcon = () => (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  );

  const LoadingSpinner = () => (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
      style={{
        width: 18,
        height: 18,
        border: "2px solid rgba(255,255,255,0.3)",
        borderTop: "2px solid #fff",
        borderRadius: "50%",
      }}
    />
  );

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <motion.button
      onClick={isConnected ? handleDisconnect : handleConnect}
      disabled={isLoading}
      whileHover={isLoading ? {} : { scale: 1.05, y: -2 }}
      whileTap={isLoading ? {} : { scale: 0.95 }}
      style={buttonStyle}
    >
      {isLoading ? (
        <>
          <LoadingSpinner />
          Connecting…
        </>
      ) : isConnected ? (
        <>
          <LogoutIcon />
          Disconnect Spotify
        </>
      ) : (
        <>
          <SpotifyIcon />
          Connect with Spotify
        </>
      )}
    </motion.button>
  );
}