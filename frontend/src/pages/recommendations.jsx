import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate, useSearchParams } from "react-router-dom";
import RecommendationCard from "../components/recommendationcard";
import Loader from "../components/loader";
import { getRecs } from "../api/recAPI";

const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 20; // 60 seconds max

// Cleanly configure the backend base path from your environment variables
const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
const BACKEND_URL = backendBaseUrl.replace(/\/$/, "");

/**
 * Polls the Hugging Face status endpoint instead of Vercel relative paths
 */
async function waitForIndexing(onProgress) {
  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
    try {
      // ✅ FIXED: Using the complete backend URL path
      const res = await fetch(`${BACKEND_URL}/api/indexing_status`);
      if (res.ok) {
        const data = await res.json();
        onProgress(data);

        // Done — store has tracks
        if (!data.running && data.store_size > 0) return true;

        // Done but empty (no tracks found or error)
        if (!data.running && data.done) return false;
      }
    } catch (err) {
      console.warn("[Indexing Status] Network tick error:", err);
      // Network hiccup — keep polling
    }
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }
  return false; // Timed out
}

export default function Recommendations() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indexingStatus, setIndexingStatus] = useState(null);
  const navigate = useNavigate();

  const [searchParams] = useSearchParams();
  const color = searchParams.get("color") || "#7C3AED";

  const loadRecs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await getRecs(color);
      const recs = res?.recommendations || [];

      const isConnected = localStorage.getItem("spotify_connected") === "true";
      if (recs.length === 0 && isConnected) {
        // ✅ FIXED: Using the complete backend URL path here too
        const statusRes = await fetch(`${BACKEND_URL}/api/indexing_status`);
        if (statusRes.ok) {
          const status = await statusRes.json();

          if (status.running) {
            setIndexingStatus(status);
            await waitForIndexing((s) => setIndexingStatus(s));
            const retryRes = await getRecs(color);
            setSongs(retryRes?.recommendations || []);
            setIndexingStatus(null);
            return;
          }
        }
      }

      setSongs(recs);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
      setError(err.message || "Something went wrong loading recommendations.");
      setSongs([]);
    } finally {
      setLoading(false);
    }
  }, [color]);

  useEffect(() => {
    loadRecs();
  }, [loadRecs]);

  // -------------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <Loader
        message={
          indexingStatus?.running
            ? `Indexing your library… ${indexingStatus.tracks_indexed ?? 0} tracks loaded`
            : "Mapping colors to emotions…"
        }
      />
    );
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        padding: "120px 24px 80px 24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        background: `radial-gradient(circle at top, ${color}33 0%, #0d0d15 100%)`,
        transition: "background 1s ease",
        position: "relative",
        overflowX: "hidden",
      }}
    >
      {/* Back button */}
      <motion.button
        onClick={() => navigate("/")}
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        whileHover={{ scale: 1.05, background: "rgba(255,255,255,0.12)" }}
        whileTap={{ scale: 0.95 }}
        style={{
          position: "fixed",
          top: "40px",
          left: "40px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "12px 20px",
          borderRadius: "999px",
          border: "1px solid rgba(255,255,255,0.2)",
          background: "rgba(255,255,255,0.06)",
          backdropFilter: "blur(15px)",
          color: "#fff",
          fontSize: "0.85rem",
          fontWeight: 600,
          cursor: "pointer",
          zIndex: 100,
          boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
        }}
      >
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
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to Wheel
      </motion.button>

      {/* Header panel */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        style={{
          padding: "32px 48px",
          marginBottom: "60px",
          borderRadius: "32px",
          textAlign: "center",
          background: "rgba(255,255,255,0.03)",
          backdropFilter: "blur(30px) saturate(160%)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderTop: "1.5px solid rgba(255,255,255,0.25)",
          boxShadow: "0 30px 60px rgba(0,0,0,0.4)",
        }}
      >
        <h2
          style={{
            fontSize: "2.2rem",
            fontWeight: 800,
            color: "#fff",
            marginBottom: "12px",
            letterSpacing: "-0.03em",
          }}
        >
          Atmospheric Mix
        </h2>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
          }}
        >
          <span style={{ color: "rgba(255,255,255,0.4)", fontWeight: 500 }}>
            Inspired by
          </span>
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              background: color,
              border: "2px solid #fff",
              boxShadow: `0 0 12px ${color}`,
            }}
          />
          <span
            style={{
              fontWeight: 700,
              color: color,
              textTransform: "uppercase",
              letterSpacing: "1.5px",
              fontSize: "0.9rem",
            }}
          >
            {color}
          </span>
        </div>
      </motion.div>

      {/* Recommendations list */}
      <motion.div
        layout
        style={{
          width: "100%",
          maxWidth: 620,
          display: "flex",
          flexDirection: "column",
          gap: "24px",
        }}
      >
        <AnimatePresence>
          {error ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                textAlign: "center",
                padding: "40px",
                color: "rgba(255,100,100,0.8)",
              }}
            >
              <p style={{ fontSize: "1rem", marginBottom: "12px" }}>{error}</p>
              <motion.button
                onClick={loadRecs}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{
                  padding: "10px 24px",
                  borderRadius: "999px",
                  border: "1px solid rgba(255,100,100,0.4)",
                  background: "rgba(255,100,100,0.1)",
                  color: "rgba(255,100,100,0.9)",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Try again
              </motion.button>
            </motion.div>
          ) : songs.length > 0 ? (
            songs.map((s, i) => (
              <RecommendationCard key={s.id || i} item={s} />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                textAlign: "center",
                padding: "40px",
                color: "rgba(255,255,255,0.3)",
              }}
            >
              <p style={{ fontSize: "1rem", marginBottom: "8px" }}>
                No tracks found for this colour yet.
              </p>
              <p style={{ fontSize: "0.8rem", marginBottom: "20px" }}>
                Connect Spotify so we can build your personal library, or try a
                different colour.
              </p>
              <motion.button
                onClick={() => navigate("/")}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{
                  padding: "10px 24px",
                  borderRadius: "999px",
                  border: "1px solid rgba(255,255,255,0.2)",
                  background: "rgba(255,255,255,0.06)",
                  color: "rgba(255,255,255,0.6)",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Pick another colour
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}