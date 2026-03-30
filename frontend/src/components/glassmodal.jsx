// src/components/SmallColorIcon.jsx
import React from "react";

export default function SmallColorIcon({ size = 48, onClick = () => {} }) {
  const ringStyle = {
    width: size,
    height: size,
    borderRadius: "50%",
    padding: 3,
    
    // 1. The "Glow" - instead of a flat gradient, make it look like an internal light
    background: `conic-gradient(
      from 180deg at 50% 50%, 
      #FFD6E8 0deg, #F6DDE8 60deg, #D8C2CC 120deg, 
      #EEF7F4 180deg, #B9A3AE 240deg, #FFD6E8 360deg
    )`,
    
    // 2. The "Refraction" - add a crisp white border highlight
    border: "1.5px solid rgba(255, 255, 255, 0.4)",
    
    // 3. The "Deep Shadow" - makes it pop off the glass
    boxShadow: `
      0 10px 25px rgba(0,0,0,0.1), 
      inset 0 0 10px rgba(255,255,255,0.5)
    `,

    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)",
  };

  const centerStyle = {
    width: "60%",
    height: "60%",
    borderRadius: "50%",
    
    // 4. The "Glass Topper" - makes the center look like a concave button
    background: "rgba(255, 255, 255, 0.7)",
    backdropFilter: "blur(4px)",
    boxShadow: "inset 0 2px 4px rgba(0,0,0,0.1), 0 1px 0 rgba(255,255,255,0.8)",
  };

  return (
    <button
      onClick={onClick}
      onMouseEnter={(e) => (e.currentTarget.firstChild.style.transform = "scale(1.15) rotate(15deg)")}
      onMouseLeave={(e) => (e.currentTarget.firstChild.style.transform = "scale(1) rotate(0deg)")}
      style={{ border: "none", background: "transparent", padding: 10 }}
    >
      <div style={ringStyle}>
        <div style={centerStyle} />
      </div>
    </button>
  );
}