import React from "react";

export default function Navbar() {
  return (
    <div
      className="glass"
      style={{
        width: "100%",
        padding: "16px 28px",

        display: "flex",
        alignItems: "center",
        justifyContent: "center",

        position: "sticky",
        top: 0,
        zIndex: 20,

        borderRadius: "0 0 28px 28px",
        boxShadow: "0 12px 40px rgba(0,0,0,0.08)",
      }}
    >
      <div
        style={{
          fontSize: "1.6rem",
          fontWeight: 500,
          letterSpacing: "0.6px",
          color: "#7F8582", // warm gray
        }}
      >
        Shikisai
      </div>
    </div>
  );
}
