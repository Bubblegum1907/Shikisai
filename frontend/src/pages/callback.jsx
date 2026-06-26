import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";

const BACKEND = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

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
    console.log("[Shikisai] Background indexing triggered from callback.");
  } catch (err) {
    console.warn("[Shikisai] Indexing trigger failed (non-fatal):", err);
  }
}

/**
 * Callback
 *
 * Landing page after Spotify OAuth redirect.
 *
 * Fixes:
 * - Uses useSearchParams() instead of window.location.search
 * - Shows a proper error screen if tokens are missing instead of
 *   silently redirecting to home with a broken state
 * - Triggers background indexing immediately after storing tokens
 * - Shows connecting animation while processing
 */
export default function Callback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = searchParams.get("token");
    const refreshToken = searchParams.get("refresh_token");

    if (!token || !refreshToken) {
      setError(
        "Spotify authorisation failed — no tokens received. " +
          "Please try connecting again."
      );
      return;
    }

    // Store tokens
    localStorage.setItem("spotify_token", token);
    localStorage.setItem("spotify_refresh_token", refreshToken);
    localStorage.setItem("spotify_connected", "true");
    // Clear stale indexing flag so fresh indexing runs
    localStorage.removeItem("indexing_triggered");

    // Kick off background indexing then go home
    triggerIndexing(token).then(() => {
      localStorage.setItem("indexing_triggered", "true");
      navigate("/");
    });
  }, [searchParams, navigate]);

  // -------------------------------------------------------------------------
  // Error state
  // -------------------------------------------------------------------------
  if (error) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: "24px",
          background: "radial-gradient(circle at center, #1a1a2e 0%, #0d0d15 100%)",
          padding: "40px",
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            textAlign: "center",
            maxWidth: 480,
            padding: "40px",
            borderRadius: "24px",
            background: "rgba(239,68,68,0.08)",
            border: "1px solid rgba(239,68,68,0.25)",
          }}
        >
          <p
            style={{
              color: "#F87171",
              fontSize: "1rem",
              lineHeight: 1.6,
              marginBottom: "24px",
            }}
          >
            {error}
          </p>
          <motion.button
            onClick={() => navigate("/")}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: "12px 28px",
              borderRadius: "999px",
              border: "1px solid rgba(255,255,255,0.2)",
              background: "rgba(255,255,255,0.06)",
              color: "#fff",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "0.9rem",
            }}
          >
            Back to home
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Loading / connecting state
  // -------------------------------------------------------------------------
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: "24px",
        background: "radial-gradient(circle at center, #1a1a2e 0%, #0d0d15 100%)",
      }}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
        style={{
          width: 48,
          height: 48,
          border: "3px solid rgba(124,58,237,0.2)",
          borderTop: "3px solid #7C3AED",
          borderRadius: "50%",
        }}
      />
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.4, 0.9, 0.4] }}
        transition={{ duration: 2, repeat: Infinity }}
        style={{
          color: "rgba(255,255,255,0.5)",
          fontSize: "0.95rem",
          fontWeight: 500,
          letterSpacing: "1px",
        }}
      >
        Connecting to Spotify…
      </motion.p>
    </div>
  );
}