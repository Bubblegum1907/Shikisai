import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

export default function SpotifyAuthButton() {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    const connected = localStorage.getItem("spotify_connected") === "true";
    setIsConnected(connected);
  }, []);

  const handleAuth = () => {
    if (isConnected) {
      // LOGOUT LOGIC
      localStorage.removeItem("spotify_token");
      localStorage.removeItem("spotify_refresh_token");
      localStorage.setItem("spotify_connected", "false");
      setIsConnected(false);
      // Optional: Redirect to home or refresh
      window.location.href = "/";
    } else {
      // LOGIN LOGIC
      window.location.href = "http://127.0.0.1:8000/auth/login";
    }
  };

  return (
    <motion.button
      onClick={handleAuth}
      whileHover={{ scale: 1.05, y: -2 }}
      whileTap={{ scale: 0.95 }}
      style={{
        position: "relative",
        padding: "14px 32px",
        borderRadius: "999px",
        fontSize: "0.95rem",
        fontWeight: 600,
        cursor: "pointer",
        
        // DYNAMIC STYLING: Shift colors based on state
        background: isConnected 
          ? "rgba(239, 68, 68, 0.15)" // Subtle Red for Logout
          : "rgba(124, 58, 237, 0.25)", // Indigo for Login
          
        backdropFilter: "blur(12px) saturate(150%)",
        color: isConnected ? "#F87171" : "#FFFFFF",
        
        border: isConnected 
          ? "1px solid rgba(239, 68, 68, 0.3)" 
          : "1px solid rgba(255, 255, 255, 0.3)",
          
        boxShadow: isConnected
          ? "0 10px 25px -5px rgba(239, 68, 68, 0.2)"
          : "0 10px 25px -5px rgba(124, 58, 237, 0.4)",
        
        transition: "all 0.3s ease",
        display: "flex",
        alignItems: "center",
        gap: "10px"
      }}
    >
      {/* Icon shifts based on state */}
      {isConnected ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.508 17.302c-.218.358-.683.472-1.042.254-2.812-1.718-6.353-2.106-10.518-1.157-.409.094-.818-.163-.912-.572-.094-.409.163-.818.572-.912 4.582-1.048 8.491-.597 11.646 1.33.359.219.473.684.254 1.041zm1.468-3.258c-.274.444-.852.585-1.296.311-3.218-1.977-8.125-2.551-11.93-1.397-.502.152-1.03-.135-1.182-.637-.152-.502.135-1.03.637-1.182 4.344-1.317 9.757-.674 13.46 1.601.444.274.585.852.311 1.296zm.128-3.395c-.33.539-1.033.709-1.572.38-3.824-2.272-10.126-2.481-13.784-1.371-.62.188-1.269-.168-1.457-.788-.188-.62.168-1.269.788-1.457 4.312-1.308 11.272-1.064 15.651 1.537.536.318.706 1.021.38 1.56z"/>
        </svg>
      )}

      {isConnected ? "Disconnect Spotify" : "Connect with Spotify"}
    </motion.button>
  );
}