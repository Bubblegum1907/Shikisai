import React from "react";
import { motion } from "framer-motion";

export default function RecommendationCard({ item }) {
  // 1. Bulletproof Spotify Link & Artist Logic
  const trackId = item.id || item.spotify_id;
  const spotifyLink = trackId ? `https://open.spotify.com/track/${trackId}` : "#";

  const artistDisplay = React.useMemo(() => {
    if (!item.artists) return "Unknown Artist";
    if (Array.isArray(item.artists)) return item.artists.join(", ");
    // Clean strings like "['Artist Name']" or "Artist1, Artist2"
    return item.artists.replace(/[\[\]']/g, "").trim();
  }, [item.artists]);

  // 2. Dynamic Glow Logic (Uses VAD scores if available to tint the card)
  const glowColor = item.valence > 0.5 
    ? "rgba(245, 158, 11, 0.2)"  // Warm amber for high valence
    : "rgba(124, 58, 237, 0.15)"; // Moody violet for lower valence

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -10, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="relative overflow-hidden"
      style={{
        marginBottom: "24px",
        padding: "40px",
        borderRadius: "40px",
        background: "linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04))",
        backdropFilter: "blur(24px) saturate(180%)",
        WebkitBackdropFilter: "blur(24px) saturate(180%)",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderTop: "1.5px solid rgba(255, 255, 255, 0.35)",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
      }}
    >
      {/* Dynamic Background Glow */}
      <div 
        style={{
          position: "absolute",
          top: "-30%",
          right: "-10%",
          width: "70%",
          height: "90%",
          background: `radial-gradient(circle, ${glowColor} 0%, transparent 80%)`,
          filter: "blur(40px)",
          pointerEvents: "none",
          zIndex: 0
        }}
      />

      <div className="relative z-10">
        <h3
          style={{
            fontWeight: 800,
            fontSize: "1.4rem",
            marginBottom: "6px",
            letterSpacing: "-0.03em",
            color: "#FFFFFF",
            textShadow: "0 4px 12px rgba(0,0,0,0.3)"
          }}
        >
          {item.name}
        </h3>

        <p
          style={{
            fontSize: "1rem",
            marginBottom: "32px",
            fontWeight: 500,
            color: "rgba(255, 255, 255, 0.55)",
            letterSpacing: "0.01em"
          }}
        >
          {artistDisplay}
        </p>

        <motion.a
          href={spotifyLink}
          target="_blank"
          rel="noopener noreferrer"
          whileHover={{ 
            scale: 1.05, 
            backgroundColor: "rgba(255, 255, 255, 0.3)",
            boxShadow: "0 0 20px rgba(255, 255, 255, 0.2)" 
          }}
          whileTap={{ scale: 0.95 }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "10px",
            padding: "14px 28px",
            borderRadius: "100px",
            background: "rgba(255, 255, 255, 0.15)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.3)",
            fontWeight: 700,
            fontSize: "0.85rem",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "#FFFFFF",
            textDecoration: "none",
            transition: "all 0.3s ease",
          }}
        >
          Listen on Spotify
        </motion.a>
      </div>
    </motion.div>
  );
}