import React from "react";
import { motion } from "framer-motion";

export default function Navbar() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="glass"
      style={{
        width: "100%",
        padding: "20px 40px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between", // Better for adding nav links later
        position: "sticky",
        top: 0,
        zIndex: 100,

        // THE LIQUID GLASS STRIP
        background: "rgba(255, 255, 255, 0.08)", 
        backdropFilter: "blur(20px) saturate(140%)",
        WebkitBackdropFilter: "blur(20px) saturate(140%)",
        
        // The "Border Glow" instead of a heavy shadow
        borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
        
        // Soft illumination shadow
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.05)",
        borderRadius: "0 0 32px 32px",
      }}
    >
      {/* Logo Area */}
      <div
        style={{
          fontSize: "1.4rem",
          fontWeight: 700,
          letterSpacing: "1.5px",
          textTransform: "uppercase",
          // Gradient text to match the Shikisai vibe
          background: "linear-gradient(90deg, #7C3AED, #2DD4BF)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        Shikisai
      </div>

      {/* Modern minimalist indicator (Recruiter flex: shows you think about state) */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          background: "#2DD4BF",
          boxShadow: "0 0 10px #2DD4BF"
        }} />
        <span style={{ 
          fontSize: "0.75rem", 
          color: "rgba(255,255,255,0.6)", 
          fontWeight: 500,
          letterSpacing: "1px" 
        }}>
          AI ACTIVE
        </span>
      </div>
    </motion.nav>
  );
}