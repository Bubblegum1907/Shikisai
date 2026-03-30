import React, { useEffect, useState } from "react";
import { motion } from "framer-motion"; 
import { useNavigate } from "react-router-dom";
import RecommendationCard from "../components/recommendationcard";
import Loader from "../components/loader";
import { getRecs } from "../api/recAPI";

export default function Recommendations() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Get color from URL
  const params = new URLSearchParams(window.location.search);
  const color = params.get("color") || "#7C3AED"; 

  useEffect(() => {
    async function load() {
      try {
        const res = await getRecs(color);
        setSongs(res?.recommendations || []);
      } catch (err) {
        console.error("Failed to load recommendations:", err);
        setSongs([]);
      } finally {
        setLoading(false);
      }
    }

    if (color) load();
    else setLoading(false);
  }, [color]);

  if (loading) return <Loader />;

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        padding: "120px 24px 80px 24px", // Extra top padding for the fixed button
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        background: `radial-gradient(circle at top, ${color}33 0%, #0d0d15 100%)`, 
        transition: "background 1s ease",
        position: "relative",
        overflowX: "hidden"
      }}
    >
      {/* --- BACK BUTTON --- */}
      <motion.button
        onClick={() => navigate("/")}
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        whileHover={{ scale: 1.05, background: "rgba(255, 255, 255, 0.12)" }}
        whileTap={{ scale: 0.95 }}
        style={{
          position: "fixed", // Stays in view as you scroll
          top: "40px",
          left: "40px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "12px 20px",
          borderRadius: "999px",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          background: "rgba(255, 255, 255, 0.06)",
          backdropFilter: "blur(15px)",
          color: "#fff",
          fontSize: "0.85rem",
          fontWeight: 600,
          cursor: "pointer",
          zIndex: 100,
          boxShadow: "0 10px 30px rgba(0,0,0,0.2)"
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Back to Wheel
      </motion.button>

      {/* --- HEADER PANEL --- */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        style={{
          padding: "32px 48px",
          marginBottom: "60px",
          borderRadius: "32px",
          textAlign: "center",
          background: "rgba(255, 255, 255, 0.03)",
          backdropFilter: "blur(30px) saturate(160%)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderTop: "1.5px solid rgba(255, 255, 255, 0.25)", // Subtle light catch
          boxShadow: "0 30px 60px rgba(0,0,0,0.4)"
        }}
      >
        <h2 style={{ fontSize: "2.2rem", fontWeight: 800, color: "#fff", marginBottom: "12px", letterSpacing: "-0.03em" }}>
          Atmospheric Mix
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
          <span style={{ color: "rgba(255,255,255,0.4)", fontWeight: 500 }}>Inspired by</span>
          <div style={{ 
            width: 14, 
            height: 14, 
            borderRadius: '50%', 
            background: color, 
            border: '2px solid #fff',
            boxShadow: `0 0 12px ${color}` 
          }} />
          <span style={{ fontWeight: 700, color: color, textTransform: 'uppercase', letterSpacing: '1.5px', fontSize: '0.9rem' }}>
            {color}
          </span>
        </div>
      </motion.div>

      {/* --- RECOMMENDATIONS LIST --- */}
      <motion.div
        layout 
        style={{ 
          width: "100%", 
          maxWidth: 620, 
          display: "flex", 
          flexDirection: "column", 
          gap: "24px" 
        }}
      >
        {songs.length > 0 ? (
          songs.map((s, i) => (
            <RecommendationCard key={s.id || i} item={s} />
          ))
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255,255,255,0.3)' }}>
            <p>The AI is still feeling the vibes...</p>
            <p style={{ fontSize: '0.8rem' }}>Try picking a different color!</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}