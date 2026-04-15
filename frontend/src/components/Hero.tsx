"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import MultilingualTitle from "./MultilingualTitle";

export function Hero() {
  const { user, signInWithGoogle } = useAuth();
  const router = useRouter();

  const handleGetStarted = async () => {
    if (user) {
      router.push("/home");
    } else {
      await signInWithGoogle();
    }
  };

  return (
    <section className="flex flex-col items-center text-center py-20 max-w-[1200px] mx-auto px-6">
      <div className="mb-4">
        <MultilingualTitle />
      </div>
      
      <p className="body-standard max-w-[620px] mb-12 opacity-0 animate-cursor [animation-delay:400ms]">
        The world's most capable multilingual voice assistant. 
        Real-time intelligence in 22+ Indian languages with sub-800ms latency.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 opacity-0 animate-cursor [animation-delay:600ms]">
        <button 
          onClick={handleGetStarted}
          className="cursor-button-primary text-[15px] px-10 py-3 bg-cur-surface-300 border border-border-medium shadow-sm hover:shadow-md transition-all font-medium"
        >
          Get Started
        </button>
        <button className="bg-transparent border border-border-primary text-border-strong font-medium rounded-lg px-10 py-3 hover:bg-cur-surface-100 transition-all hover:text-cursor-dark">
          View Documentation
        </button>
      </div>

      <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-6 w-full opacity-0 animate-cursor [animation-delay:800ms]">
        {[
          { title: "Ultra-Low Latency", desc: "Responses in under 800ms for natural, fluid conversation." },
          { title: "22+ Languages", desc: "Native support for Hindi, Tamil, Telugu, and more." },
          { title: "LLM Powered", desc: "Sophisticated reasoning with the Sarvam-105b model." }
        ].map((feature, i) => (
          <div key={i} className="cursor-card p-8 text-left group cursor-default">
            <h3 className="section-heading !text-[24px] mb-3 group-hover:text-cur-error transition-colors">{feature.title}</h3>
            <p className="body-standard !text-[15px] leading-relaxed">{feature.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
