import React from "react";

export default function RecommendationCard({ item }) {
  const artists =
    typeof item.artists === "string"
      ? item.artists.replace(/[\[\]']/g, "")
      : Array.isArray(item.artists)
      ? item.artists.join(", ")
      : "Unknown artist";

  return (
    <div
      className="glass"
      style={{
        marginBottom: 22,
        padding: "22px 24px",
        borderRadius: "22px",
        transition: "transform 0.2s ease, box-shadow 0.2s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-4px)";
        e.currentTarget.style.boxShadow =
          "0 26px 64px rgba(100, 90, 200, 0.12)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow =
          "0 22px 60px rgba(100, 90, 200, 0.08)";
      }}
    >
      {/* Title */}
      <div
        style={{
          fontWeight: 600,
          fontSize: "1.05rem",
          marginBottom: 6,
          letterSpacing: "0.25px",

          /* pastel indigo */
          color: "#6A5AE0",
        }}
      >
        {item.name}
      </div>

      {/* Artists */}
      <div
        style={{
          fontSize: "0.92rem",
          marginBottom: 16,

          /* lavender-neutral */
          color: "#7A6FA8",
        }}
      >
        {artists}
      </div>

      {/* Spotify Button */}
      <a
        href={item.external_url}
        target="_blank"
        rel="noreferrer"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "11px 22px",
          borderRadius: "999px",

          /* brighter accent gradient */
          background: "linear-gradient(135deg, #FADADD, #E0E7FF)",

          fontWeight: 600,
          fontSize: "0.9rem",

          /* indigo accent */
          color: "#5A4FCF",
          textDecoration: "none",

          boxShadow: "0 8px 22px rgba(90, 80, 200, 0.18)",
          transition: "transform 0.15s ease, box-shadow 0.15s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "scale(1.06)";
          e.currentTarget.style.boxShadow =
            "0 12px 28px rgba(90, 80, 200, 0.28)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "scale(1)";
          e.currentTarget.style.boxShadow =
            "0 8px 22px rgba(90, 80, 200, 0.18)";
        }}
      >
        Listen
      </a>
    </div>
  );
}
