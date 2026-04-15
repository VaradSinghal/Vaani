"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { useAuth } from "@/context/AuthContext";
import { AgentStatusDemo } from "@/components/AgentStatusDemo";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push("/home");
    }
  }, [user, loading, router]);

  return (
    <div className="flex flex-col min-h-screen bg-cur-cream selection:bg-cur-orange/20 selection:text-cur-orange transition-colors duration-300">
      <Navbar />
      
      <main className="flex-1">
        {/* Main Hero Wrapper */}
        <section className="relative overflow-visible">
          <Hero />
        </section>

        {/* Section: Literary Depth (Serif) */}
        <section className="bg-cur-surface-300 border-y border-border-primary py-32">
          <div className="max-w-[1200px] mx-auto px-6 text-center">
            <h2 className="section-heading mb-10">Linguistic Craft.</h2>
            <div className="max-w-[800px] mx-auto space-y-8">
              <p className="body-serif text-cursor-dark">
                Vaani goes beyond mere translation. We've built an engine that captures the prosody and intent of Indian languages 
                with the same care as a finely printed manuscript. 
              </p>
              <p className="body-standard max-w-[600px] mx-auto italic">
                “Language is the architecture of thought, and we are building for a billion thoughts at once.”
              </p>
            </div>
            
            <div className="mt-20 flex flex-wrap justify-center gap-3">
              {["हिंदी", "தமிழ்", "తెలుగు", "मराठी", "বাংলা", "ಕನ್ನಡ", "മലയാളം", "ગુજરાતી", "ਪੰਜਾਬီ"].map((lang, i) => (
                <div key={i} className="cursor-pill bg-cur-cream border border-border-primary hover:border-border-medium shadow-sm transition-all">
                  {lang}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* The Voice Agent Preview (Static) */}
        <div className="bg-cur-cream">
           <AgentStatusDemo />
        </div>

        {/* Technical/Code Section */}
        <section className="py-32 bg-cur-surface-500 border-t border-border-primary">
          <div className="max-w-[1200px] mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
              <div>
                <span className="font-mono text-[11px] uppercase tracking-widest text-border-strong mb-6 block">API Reference</span>
                <h2 className="section-heading mb-8">Programmatic Voice.</h2>
                <div className="space-y-6 text-border-strong font-editorial text-[18px]">
                   <p>Our WebSocket protocol allows you to stream raw audio and receive structured linguistic metadata in real-time.</p>
                   <p className="text-[15px] font-sans">Designed for developers building the next generation of voice-first interfaces.</p>
                </div>
                
                <div className="mt-12 flex gap-4">
                   <button className="cursor-button-primary border border-border-medium hover:bg-cur-cream">API Docs</button>
                   <button className="px-6 py-2.5 text-[14px] font-medium text-cursor-dark hover:text-cur-orange transition-colors">SDK Guide</button>
                </div>
              </div>
              
              {/* Code Snapshot in Cursor style */}
              <div className="cursor-card bg-[#0d0d0d] p-0 shadow-2xl overflow-hidden border-border-strong/20">
                <div className="h-8 bg-[#1a1a1a] flex items-center px-4 gap-1.5 border-b border-white/5">
                   <div className="w-2.5 h-2.5 rounded-full bg-white/10"></div>
                   <div className="w-2.5 h-2.5 rounded-full bg-white/10"></div>
                   <div className="w-2.5 h-2.5 rounded-full bg-white/10"></div>
                </div>
                <div className="p-8 font-mono text-[12px] text-[#9fbbe0] leading-relaxed">
                  <pre>
                    <code>{`
const vaani = new VaaniClient({
  apiKey: process.env.VAANI_API_KEY
});

// Stream 16kHz PCM audio
const stream = await vaani.voice.connect();

stream.on('transcript', (data) => {
  console.log(\`[ASR] \${data.text}\`);
});

stream.on('audio', (chunk) => {
  player.play(chunk);
});
                    `}</code>
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border-primary py-24 bg-cur-cream">
        <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row justify-between gap-16">
          <div className="space-y-6">
            <div className="flex items-center gap-1.5">
              <div className="w-5 h-5 bg-cursor-dark rounded-[4px] flex items-center justify-center">
                <span className="text-cur-cream font-bold text-[10px]">V</span>
              </div>
              <span className="font-sans font-bold tracking-tight text-[15px] text-cursor-dark">Vaani</span>
            </div>
            <p className="max-w-[280px] body-standard !text-[14px]">
              Crafting linguistic intelligence for the Indian subcontinent. Focused on latency, empathy, and craft.
            </p>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-16">
            <FooterColumn title="Identity" links={["Models", "Datasets", "Safety"]} />
            <FooterColumn title="Resources" links={["Documentation", "API Explorer", "Changelog"]} />
            <FooterColumn title="Craft" links={["The Studio", "Brand", "Journal"]} />
          </div>
        </div>
        <div className="max-w-[1200px] mx-auto px-6 mt-20 font-mono text-[11px] text-border-primary uppercase tracking-widest text-center">
           © 2026 Vaani AI. Engineered with Warmth.
        </div>
      </footer>
    </div>
  );
}

function FooterColumn({ title, links }: { title: string, links: string[] }) {
  return (
    <div className="space-y-6">
      <h4 className="font-mono text-[11px] uppercase tracking-widest text-border-strong opacity-40">{title}</h4>
      <ul className="space-y-3">
        {links.map((link) => (
          <li key={link}>
            <a href="#" className="font-sans text-[14px] text-border-strong hover:text-cur-orange transition-colors">
              {link}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
