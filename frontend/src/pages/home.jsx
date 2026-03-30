import React, { useEffect, useState } from "react";
import SpotifyAuthButton from "../components/LoginButton"; 
import ColorWheel from "../components/colorwheel";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

export default function Home() {
  const navigate = useNavigate();
  const [connected, setConnected] = useState(false);
  const WHEEL_SIZE = 400; // Defined here to avoid reference errors

  useEffect(() => {
    const isConnected = localStorage.getItem("spotify_connected") === "true";
    setConnected(isConnected);

    const handleStorage = () => {
      setConnected(localStorage.getItem("spotify_connected") === "true");
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const handlePick = (hex) => {
    navigate(`/recommendations?color=${encodeURIComponent(hex)}`);
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        minHeight: "100vh",
        width: "100%",
        background: "radial-gradient(circle at center, #1a1a2e 0%, #0d0d15 100%)",
        display: "flex", 
        flexDirection: "column", 
        justifyContent: "center", 
        alignItems: "center",
        gap: "48px", 
        padding: "40px 20px",
        overflow: "hidden",
        position: "relative"
      }}
    >
      {/* 1. BRANDING AREA */}
      <div style={{ textAlign: 'center', zIndex: 10 }}>
        <motion.h1 
          initial={{ y: -20, opacity: 0 }} 
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{ 
            fontSize: "4.5rem", 
            fontWeight: 800, 
            letterSpacing: "-0.06em",
            background: "linear-gradient(to bottom, #ffffff 40%, rgba(255,255,255,0.2) 100%)",
            WebkitBackgroundClip: "text", 
            WebkitTextFillColor: "transparent",
            marginBottom: "4px"
          }}
        >
          Shikisai
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.4 }}
          transition={{ delay: 0.4 }}
          style={{ color: "#fff", fontSize: "0.75rem", letterSpacing: "4px", textTransform: "uppercase" }}
        >
          Chromesthesia for your ears
        </motion.p>
      </div>

      {/* 2. AUTHENTICATION BUTTON */}
      <SpotifyAuthButton />

      {/* 3. INTERACTIVE WHEEL AREA */}
      <motion.div 
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        style={{ position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}
      >
        {/* Dynamic Background Glow - Perfectly Centered */}
        <motion.div 
          animate={{ 
            rotate: 360,
            scale: [1, 1.15, 1]
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          style={{
            position: 'absolute', 
            width: WHEEL_SIZE * 0.85, 
            height: WHEEL_SIZE * 0.85,
            filter: 'blur(70px)', 
            opacity: 0.2,
            background: 'conic-gradient(from 0deg, #7C3AED, #2DD4BF, #EC4899, #7C3AED)',
            borderRadius: '50%', 
            zIndex: -1
          }} 
        />
        
        {/* The Color Wheel */}
        <ColorWheel size={WHEEL_SIZE} onPick={handlePick} />
      </motion.div>

      {/* 4. FOOTER HINT */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}
      >
        <motion.span 
          animate={{ opacity: [0.2, 0.5, 0.2], y: [0, 5, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          style={{ 
            color: "rgba(255,255,255,0.4)", 
            fontSize: "0.7rem", 
            fontWeight: 600, 
            letterSpacing: '2px',
            textTransform: 'uppercase'
          }}
        >
          Tap the wheel to begin
        </motion.span>
      </motion.div>
    </motion.div>
  );
}