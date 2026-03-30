import React, { useRef, useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import VIBE_DATA from "../data/colors_to_feelings.json";

export default function ColorWheel({ size = 420, knobSize = 28, onPick }) {
  const canvasRef = useRef(null);
  const wrapperRef = useRef(null);
  const lastHexRef = useRef("#FAF0F0");

  const [dragging, setDragging] = useState(false);
  const [luminance, setLuminance] = useState(0.95);
  const [selector, setSelector] = useState({
    x: size / 2,
    y: size / 2,
    hex: "#FAF0F0",
  });

  const dpi = window.devicePixelRatio || 1;

  // 1. Prepare Vibe Data
  const memoizedVibes = useMemo(() => {
    return Object.entries(VIBE_DATA).map(([hex, vibe]) => ({
      rgb: hexToRgb(hex),
      vibe: vibe
    }));
  }, []);

  // 2. Draw Wheel
  useEffect(() => {
    const canvas = canvasRef.current;
    const real = size * dpi;
    canvas.width = real;
    canvas.height = real;
    canvas.style.width = size + "px";
    canvas.style.height = size + "px";

    const ctx = canvas.getContext("2d");
    const radius = size / 2;
    const realRadius = real / 2;
    const img = ctx.createImageData(real, real);
    const data = img.data;

    for (let y = 0; y < real; y++) {
      for (let x = 0; x < real; x++) {
        const dx = x - realRadius;
        const dy = y - realRadius;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const i = (y * real + x) * 4;

        if (dist > realRadius) {
          data[i + 3] = 0;
          continue;
        }

        const lx = dx / dpi;
        const ly = dy / dpi;
        const sat = Math.min(Math.sqrt(lx * lx + ly * ly) / radius, 1);

        let angle = Math.atan2(ly, lx);
        if (angle < 0) angle += 2 * Math.PI;
        const hue = (angle * 180) / Math.PI;

        let val;
        if (sat > 0.85) val = 1 + (sat - 0.85) * 0.5;
        else if (sat > 0.4) val = 0.95;
        else val = 0.7 + sat * 0.6;

        const finalVal = Math.min(val * luminance, 1);
        const [r, g, b] = hsvToRgb(hue, sat ** 0.92, finalVal);

        data[i] = r * 255;
        data[i + 1] = g * 255;
        data[i + 2] = b * 255;
        data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [size, luminance, dpi]);

  // 3. Picking Logic
  const pickColor = (event) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    let x, y;

    if (event.nativeEvent?.offsetX != null) {
      x = event.nativeEvent.offsetX;
      y = event.nativeEvent.offsetY;
    } else if ("clientX" in event) {
      x = event.clientX - rect.left;
      y = event.clientY - rect.top;
    } else if (event.touches?.length) {
      const t = event.touches[0];
      x = t.clientX - rect.left;
      y = t.clientY - rect.top;
    } else return;

    const dx = x - size / 2;
    const dy = y - size / 2;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const radius = size / 2;

    let ndx = dx, ndy = dy;
    if (dist > radius) {
      const s = radius / dist;
      ndx *= s;
      ndy *= s;
    }

    let angle = Math.atan2(ndy, ndx);
    if (angle < 0) angle += Math.PI * 2;

    const hue = (angle * 180) / Math.PI;
    const sat = Math.min(Math.sqrt(ndx * ndx + ndy * ndy) / radius, 1);

    let val;
    if (sat > 0.85) val = 1 + (sat - 0.85) * 0.5;
    else if (sat > 0.4) val = 0.95;
    else val = 0.7 + sat * 0.6;

    const finalVal = Math.min(val * luminance, 1);
    const [r, g, b] = hsvToRgb(hue, sat ** 0.92, finalVal);
    const hex = rgbToHex(r * 255, g * 255, b * 255);
    lastHexRef.current = hex;

    setSelector({ x: size / 2 + ndx, y: size / 2 + ndy, hex });
  };

  // 4. Drag Lifecycle
  const startDrag = (e) => {
    setDragging(true);
    pickColor(e);
  };

  useEffect(() => {
    const move = (e) => dragging && pickColor(e);
    const stop = () => {
      if (!dragging) return;
      setDragging(false);
      onPick?.(lastHexRef.current);
    };

    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", stop);
    window.addEventListener("touchmove", move, { passive: false });
    window.addEventListener("touchend", stop);

    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", stop);
      window.removeEventListener("touchmove", move);
      window.removeEventListener("touchend", stop);
    };
  }, [dragging, onPick]);

  const getDetailedVibe = (currentHex) => {
    const target = hexToRgb(currentHex);
    let closestVibe = "";
    let minDistance = Infinity;

    for (const item of memoizedVibes) {
      const distance = Math.sqrt(
        Math.pow(target.r - item.rgb.r, 2) +
        Math.pow(target.g - item.rgb.g, 2) +
        Math.pow(target.b - item.rgb.b, 2)
      );
      if (distance < minDistance) {
        minDistance = distance;
        closestVibe = item.vibe;
      }
    }
    return closestVibe;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24, alignItems: "center" }}>
      <div style={{ textAlign: "center", height: 40 }}> 
        <motion.h2 
          key={getDetailedVibe(selector.hex)}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ 
            margin: 0, 
            fontSize: "1.2rem", 
            color: selector.hex, 
            textTransform: "uppercase", 
            letterSpacing: "2px",
            textShadow: "0 0 20px rgba(255,255,255,0.1)",
            transition: "color 0.3s ease" 
          }}
        >
          {getDetailedVibe(selector.hex)}
        </motion.h2>
      </div>

      <div style={{ display: "flex", gap: 32, alignItems: "center" }}>
        <div
          ref={wrapperRef}
          style={{
            width: size,
            height: size,
            position: "relative",
            borderRadius: "50%",
            background: "radial-gradient(circle, #FAF0F0, #EEF7F4)",
            boxShadow: "0 30px 80px rgba(0,0,0,0.10)",
          }}
        >
          <canvas
            ref={canvasRef}
            onMouseDown={startDrag}
            onTouchStart={startDrag}
            style={{
              width: size,
              height: size,
              borderRadius: "50%",
              cursor: "pointer",
              border: "4px solid rgba(250,240,240,0.9)",
            }}
          />
          <motion.div
            animate={{
              left: selector.x - knobSize / 2,
              top: selector.y - knobSize / 2,
            }}
            transition={dragging ? { duration: 0 } : { type: "spring", stiffness: 1600, damping: 100 }}
            style={{
              position: "absolute",
              width: knobSize,
              height: knobSize,
              borderRadius: "50%",
              background: selector.hex,
              border: "3px solid rgba(250,240,240,0.95)",
              pointerEvents: "none",
              boxShadow: "0 10px 26px rgba(0,0,0,0.25)",
            }}
          />
        </div>

        <div className="glass" style={{ height: size * 0.75, width: 24, padding: "10px 6px", borderRadius: 20 }}>
          <input
            type="range"
            min="0.25"
            max="1"
            step="0.01"
            value={luminance}
            onChange={(e) => setLuminance(parseFloat(e.target.value))}
            style={{ writingMode: "bt-lr", WebkitAppearance: "slider-vertical", height: "100%", width: "100%" }}
          />
        </div>
      </div>
    </div>
  );
}

// UTILITY FUNCTIONS
function hsvToRgb(h, s, v) {
  const c = v * s;
  const hh = (h / 60) % 6;
  const x = c * (1 - Math.abs((hh % 2) - 1));
  let r = 0,
    g = 0,
    b = 0;

  if (hh >= 0 && hh < 1) [r, g, b] = [c, x, 0];
  else if (hh < 2) [r, g, b] = [x, c, 0];
  else if (hh < 3) [r, g, b] = [0, c, x];
  else if (hh < 4) [r, g, b] = [0, x, c];
  else if (hh < 5) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];

  const m = v - c;
  return [r + m, g + m, b + m];
}

function rgbToHex(r, g, b) {
  return (
    "#" +
    [r, g, b]
      .map((n) => Math.round(n).toString(16).padStart(2, "0"))
      .join("")
  ).toUpperCase();
}

function hexToRgb(hex) {
  const cleanHex = hex.replace('#', '');
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);
  return { r, g, b };
}