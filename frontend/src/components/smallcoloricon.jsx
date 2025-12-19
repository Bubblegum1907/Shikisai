// src/components/SmallColorIcon.jsx
import React from "react";

export default function SmallColorIcon({ size = 28, onClick = () => {} }) {
  const ringStyle = {
    width: size,
    height: size,
    borderRadius: 9999,
    padding: 2,

    background: `
      conic-gradient(
        #FFD6E8,
        #F6DDE8,
        #D8C2CC,
        #EEF7F4,
        #B9A3AE,
        #FFD6E8
      )
    `,

    boxShadow:
      "0 8px 20px rgba(0,0,0,0.08)",

    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
  };

  const centerStyle = {
    width: size * 0.56,
    height: size * 0.56,
    borderRadius: 9999,

    background: "rgba(250, 240, 240, 0.95)",

    boxShadow:
      "inset 0 1px 0 rgba(255,255,255,0.6)",
  };

  return (
    <button
      onClick={onClick}
      aria-label="select another color"
      style={{
        border: "none",
        background: "transparent",
        padding: 0,
      }}
    >
      <div style={ringStyle}>
        <div style={centerStyle} />
      </div>
    </button>
  );
}
