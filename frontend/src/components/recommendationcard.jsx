import React from "react";
import { motion } from "framer-motion";

export default function RecommendationCard({ item }) {
  // Clean up artist string
  const artists =
    typeof item.artists === "string"
      ? item.artists.replace(/[\[\]']/g, "")
      : Array.isArray(item.artists)
      ? item.artists.join(", ")
      : "Unknown artist";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        y: -8, 
        transition: { duration: 0.3, ease: "easeOut" } 
      }}
      className="relative overflow-hidden"
      style={{
        marginBottom: 24,
        padding: "32px",
        borderRadius: "32px",
        
        // THE LIQUID GLASS CORE
        background: "linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))",
        backdropFilter: "blur(20px) saturate(160%)",
        WebkitBackdropFilter: "blur(20px) saturate(160%)",
        
        // The Specular Highlight (The 2026 "Edge")
        border: "1px solid rgba(255, 255, 255, 0.2)",
        borderTop: "1.5px solid rgba(255, 255, 255, 0.4)",
        
        // Shadow that feels like light passing through glass
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.1)",
        cursor: "default"
      }}
    >
      {/* 1. The Internal "Glow" (Driven by the song's vibe) */}
      <div 
        style={{
          position: "absolute",
          top: "-20%",
          right: "-10%",
          width: "60%",
          height: "80%",
          background: "radial-gradient(circle, rgba(124, 58, 237, 0.15) 0%, transparent 70%)",
          filter: "blur(30px)",
          pointerEvents: "none"
        }}
      />

      {/* 2. Song Content */}
      <div className="relative z-10">
        <h3
          style={{
            fontWeight: 700,
            fontSize: "1.2rem",
            marginBottom: 4,
            letterSpacing: "-0.02em",
            color: "#FFFFFF", // White pops better on glass
            textShadow: "0 2px 10px rgba(0,0,0,0.2)"
          }}
        >
          {item.name}
        </h3>

        <p
          style={{
            fontSize: "0.95rem",
            marginBottom: 24,
            fontWeight: 400,
            color: "rgba(255, 255, 255, 0.6)", // Faded look for secondary text
          }}
        >
          {artists}
        </p>

        {/* 3. The "Jelly" Spotify Button */}
        <motion.a
          href={item.external_url}
          target="_blank"
          rel="noreferrer"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            padding: "12px 24px",
            borderRadius: "999px",
            
            // Matches the "Primary Button" in your Pinterest kit
            background: "rgba(255, 255, 255, 0.2)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.4)",
            
            fontWeight: 600,
            fontSize: "0.9rem",
            color: "#FFFFFF",
            textDecoration: "none",
            boxShadow: "0 8px 20px rgba(0, 0, 0, 0.1)",
          }}
        >
          Listen on Spotify
        </motion.a>
      </div>
    </motion.div>
  );
}