import React from "react";
import { motion } from "framer-motion";

export default function Loader() {
  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: "24px",
        // The background should be a deep, dark mesh to let the glass "glow"
        background: "radial-gradient(circle at center, #1a1a2e 0%, #0d0d15 100%)",
      }}
    >
      <div style={{ position: "relative", width: 140, height: 140 }}>
        {/* 1. The Outer Glow (Atmospheric) */}
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(124, 58, 237, 0.4) 0%, transparent 70%)",
            filter: "blur(20px)",
          }}
        />

        {/* 2. The Glass Orb */}
        <motion.div
          animate={{
            y: [0, -10, 0],
            rotate: [0, 5, 0],
          }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          style={{
            width: "100%",
            height: "100%",
            borderRadius: "50%",
            background: "rgba(255, 255, 255, 0.1)",
            backdropFilter: "blur(15px) saturate(180%)",
            border: "1px solid rgba(255, 255, 255, 0.4)",
            boxShadow: `
              inset 0 0 20px rgba(255, 255, 255, 0.2),
              0 20px 50px rgba(0, 0, 0, 0.3)
            `,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            position: "relative",
            zIndex: 2,
          }}
        >
          {/* 3. The Refractive "Sheen" */}
          <div
            style={{
              position: "absolute",
              top: "15%",
              left: "15%",
              width: "30%",
              height: "20%",
              background: "linear-gradient(to bottom, rgba(255,255,255,0.5), transparent)",
              borderRadius: "50%",
              transform: "rotate(-30deg)",
            }}
          />

          <span
            style={{
              color: "rgba(255, 255, 255, 0.8)",
              fontSize: "0.85rem",
              fontWeight: 600,
              letterSpacing: "2px",
              textTransform: "uppercase",
              textShadow: "0 0 10px rgba(255,255,255,0.3)",
            }}
          >
            Sensing
          </span>
        </motion.div>
      </div>

      {/* 4. The Subtitle */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.4, 0.8, 0.4] }}
        transition={{ duration: 2, repeat: Infinity }}
        style={{
          color: "#94a3b8",
          fontSize: "0.9rem",
          fontWeight: 400,
          fontFamily: "monospace",
        }}
      >
        mapping colors to emotions...
      </motion.p>
    </div>
  );
}