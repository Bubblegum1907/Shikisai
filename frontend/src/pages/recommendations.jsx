import React, { useEffect, useState } from "react";
import RecommendationCard from "../components/recommendationcard";
import Loader from "../components/loader";
import { getRecs } from "../api/recAPI";

export default function Recommendations() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);

  const params = new URLSearchParams(window.location.search);
  const color = params.get("color");

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
        padding: "56px 24px",

        /* IMPORTANT: let App.css control background */
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Header card */}
      <div
        className="glass"
        style={{
          padding: "18px 36px",
          marginBottom: "42px",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontSize: "1.8rem",
            fontWeight: 600,
            letterSpacing: "0.35px",

            /* pastel indigo */
            color: "#6A5AE0",
          }}
        >
          Your pastel playlist
        </h2>

        <p
          style={{
            marginTop: "8px",
            fontSize: "1rem",

            /* lavender-neutral */
            color: "#7A6FA8",
          }}
        >
          inspired by {color}
        </p>
      </div>

      {/* Recommendations list */}
      <div
        style={{
          width: "100%",
          maxWidth: 560,
          display: "flex",
          flexDirection: "column",
          gap: "22px",
        }}
      >
        {songs.map((s, i) => (
          <RecommendationCard key={i} item={s} />
        ))}
      </div>
    </div>
  );
}
