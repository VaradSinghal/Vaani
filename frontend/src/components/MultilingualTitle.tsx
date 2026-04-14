"use client";

import { useState, useEffect } from "react";

const languages = [
  { text: "Vaani", lang: "English" },
  { text: "वाणी", lang: "Hindi" },
  { text: "வாணி", lang: "Tamil" },
  { text: "వాణి", lang: "Telugu" },
  { text: "वाणी", lang: "Marathi" },
  { text: "বাণী", lang: "Bengali" },
];

export default function MultilingualTitle() {
  const [index, setIndex] = useState(0);
  const [fade, setFade] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setIndex((prev) => (prev + 1) % languages.length);
        setFade(true);
      }, 500); // Wait for fade out
    }, 2500); // 2s display + 0.5s transition

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative flex flex-col items-center py-24 min-h-[340px] justify-center overflow-visible">
      {/* Warm Parchment Glow Aura */}
      <div className="absolute inset-0 aura-bg pointer-events-none scale-150"></div>
      
      <div key={index} className="relative z-10 flex flex-col items-center animate-cursor">
        <h1 
          className="display-hero text-center leading-[1.05]"
        >
          {languages[index].text}
        </h1>
      </div>
    </div>
  );
}
