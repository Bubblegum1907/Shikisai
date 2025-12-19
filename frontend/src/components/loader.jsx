// src/components/loader.jsx
import React from "react";

export default function Loader() {
  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",

        /* matches global background */
        background: "linear-gradient(135deg, #FAF0F0, #EEF7F4)",
      }}
    >
      <div
        className="glass"
        style={{
          width: 120,
          height: 120,
          borderRadius: "50%",

          display: "flex",
          justifyContent: "center",
          alignItems: "center",

          animation: "softPulse 1.8s ease-in-out infinite",
        }}
      >
        <span
          style={{
            color: "#7F8582", // warm gray
            fontSize: "1rem",
            fontWeight: 500,
            letterSpacing: "0.3px",
          }}
        >
          Loading
        </span>

        <style>
          {`
          @keyframes softPulse {
            0%   { transform: scale(0.96); }
            50%  { transform: scale(1.04); }
            100% { transform: scale(0.96); }
          }
        `}
        </style>
      </div>
    </div>
  );
}
