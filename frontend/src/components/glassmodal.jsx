// src/components/glassmodal.jsx
import React from "react";
import { motion } from "framer-motion";

export default function GlassModal({ open, onClose, children }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center">
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0"
        style={{
          background: "rgba(250, 240, 240, 0.65)", // ivory wash
          backdropFilter: "blur(6px)",
        }}
        onClick={onClose}
      />

      {/* Modal */}
      <motion.div
        initial={{ y: 26, scale: 0.97, opacity: 0 }}
        animate={{ y: 0, scale: 1, opacity: 1 }}
        exit={{ y: 14, opacity: 0 }}
        className="relative z-50 glass"
        style={{
          padding: "28px",
          borderRadius: "32px",

          background: "rgba(250, 240, 240, 0.85)",

          boxShadow:
            "0 40px 90px rgba(0,0,0,0.12)",
        }}
      >
        {children}
      </motion.div>
    </div>
  );
}
