import React, { useMemo } from "react";
import { motion } from "framer-motion";

function parseArtists(raw) {
  if (!raw) return "Unknown Artist";

  if (Array.isArray(raw)) {
    return raw.filter(Boolean).join(", ");
  }

  if (typeof raw === "string") {
    // Handle Python-style stringified lists: "['Artist One', 'Artist Two']"
    if (raw.startsWith("[")) {
      try {
        const cleaned = raw
          .replace(/\[|\]/g, "")
          .split(",")
          .map((s) => s.trim().replace(/^['"]|['"]$/g, ""))
          .filter(Boolean);
        return cleaned.join(", ");
      } catch {
        // fall through to plain string
      }
    }
    return raw.trim();
  }

  return "Unknown Artist";
}

/**
 * Maps valence (0–1) and energy (0–1) to a glow colour.
 *
 * High valence + high energy  → warm gold
 * High valence + low energy   → soft rose
 * Low valence  + high energy  → electric violet
 * Low valence  + low energy   → deep blue
 */
function getGlowColor(valence = 0.5, energy = 0.5) {
  if (valence >= 0.6 && energy >= 0.6) return "rgba(245, 158, 11, 0.25)";   // gold
  if (valence >= 0.6 && energy < 0.6)  return "rgba(236, 72, 153, 0.20)";   // rose
  if (valence < 0.6  && energy >= 0.6) return "rgba(124, 58, 237, 0.25)";   // violet
  return "rgba(59, 130, 246, 0.20)";                                          // blue
}

function getSpotifyUrl(item) {
  const trackId = item.id || item.spotify_id;
  if (trackId) {
    return `https://open.spotify.com/track/${trackId}`;
  }
  // Fall back to a Spotify search so the button is never dead
  const query = encodeURIComponent(
    `${item.name || item.title || ""} ${parseArtists(item.artists)}`
  );
  return `https://open.spotify.com/search/${query}`;
}

export default function RecommendationCard({ item }) {
  const artistDisplay = useMemo(() => parseArtists(item.artists), [item.artists]);

  const valence = typeof item.valence === "number" ? item.valence : 0.5;
  const energy  = typeof item.energy  === "number" ? item.energy  : 0.5;

  const glowColor  = getGlowColor(valence, energy);
  const spotifyUrl = getSpotifyUrl(item);
  const trackName  = item.name || item.title || "Unknown Track";

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -8, scale: 1.015 }}
      transition={{ type: "spring", stiffness: 300, damping: 22 }}
      style={{
        position: "relative",
        overflow: "hidden",
        marginBottom: "8px",
        padding: "36px 40px 28px 40px",
        borderRadius: "36px",
        background:
          "linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.03))",
        backdropFilter: "blur(24px) saturate(180%)",
        WebkitBackdropFilter: "blur(24px) saturate(180%)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderTop: "1.5px solid rgba(255,255,255,0.30)",
        boxShadow: "0 20px 40px -12px rgba(0,0,0,0.3)",
      }}
    >
      {/* Ambient glow */}
      <div
        style={{
          position: "absolute",
          top: "-30%",
          right: "-10%",
          width: "70%",
          height: "90%",
          background: `radial-gradient(circle, ${glowColor} 0%, transparent 75%)`,
          filter: "blur(40px)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* Content */}
      <div style={{ position: "relative", zIndex: 1 }}>
        {/* Track name */}
        <h3
          style={{
            fontWeight: 800,
            fontSize: "1.35rem",
            marginBottom: "6px",
            letterSpacing: "-0.03em",
            color: "#FFFFFF",
            textShadow: "0 2px 8px rgba(0,0,0,0.3)",
            lineHeight: 1.25,
          }}
        >
          {trackName}
        </h3>

        {/* Artist */}
        <p
          style={{
            fontSize: "0.95rem",
            marginBottom: "28px",
            fontWeight: 500,
            color: "rgba(255,255,255,0.50)",
            letterSpacing: "0.01em",
          }}
        >
          {artistDisplay}
        </p>

        {/* Actions row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
          }}
        >
          {/* Spotify button */}
          <motion.a
            href={spotifyUrl}
            target="_blank"
            rel="noopener noreferrer"
            whileHover={{
              scale: 1.05,
              backgroundColor: "rgba(255,255,255,0.22)",
            }}
            whileTap={{ scale: 0.95 }}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "12px 24px",
              borderRadius: "100px",
              background: "rgba(255,255,255,0.12)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.25)",
              fontWeight: 700,
              fontSize: "0.8rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "#FFFFFF",
              textDecoration: "none",
              transition: "background 0.25s ease",
            }}
          >
            {/* Spotify logo mark */}
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.508 17.302c-.218.358-.683.472-1.042.254-2.812-1.718-6.353-2.106-10.518-1.157-.409.094-.818-.163-.912-.572-.094-.409.163-.818.572-.912 4.582-1.048 8.491-.597 11.646 1.33.359.219.473.684.254 1.041zm1.468-3.258c-.274.444-.852.585-1.296.311-3.218-1.977-8.125-2.551-11.93-1.397-.502.152-1.03-.135-1.182-.637-.152-.502.135-1.03.637-1.182 4.344-1.317 9.757-.674 13.46 1.601.444.274.585.852.311 1.296zm.128-3.395c-.33.539-1.033.709-1.572.38-3.824-2.272-10.126-2.481-13.784-1.371-.62.188-1.269-.168-1.457-.788-.188-.62.168-1.269.788-1.457 4.312-1.308 11.272-1.064 15.651 1.537.536.318.706 1.021.38 1.56z" />
            </svg>
            Listen on Spotify
          </motion.a>

          {/* Mood indicator */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: "5px",
              minWidth: 80,
            }}
          >
            <MoodBar label="Mood" value={valence} color="rgba(255,255,255,0.7)" />
            <MoodBar label="Energy" value={energy} color={glowColor.replace(/[\d.]+\)$/, "0.9)")} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/** Small labelled progress bar showing a 0–1 value */
function MoodBar({ label, value, color }) {
  return (
    <div style={{ width: "100%", textAlign: "right" }}>
      <span
        style={{
          fontSize: "0.6rem",
          fontWeight: 600,
          color: "rgba(255,255,255,0.3)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          display: "block",
          marginBottom: "3px",
        }}
      >
        {label}
      </span>
      <div
        style={{
          width: 80,
          height: 3,
          borderRadius: 4,
          background: "rgba(255,255,255,0.08)",
          overflow: "hidden",
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(value * 100)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{
            height: "100%",
            borderRadius: 4,
            background: color,
          }}
        />
      </div>
    </div>
  );
}