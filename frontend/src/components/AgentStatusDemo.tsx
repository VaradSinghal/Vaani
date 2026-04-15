"use client";

import { useAuth } from "@/context/AuthContext";

export function AgentStatusDemo() {
  const { signInWithGoogle } = useAuth();
  
  // Static mock states for the demo
  const status = "idle";
  const transcripts = [
    "User: नमस्ते, आप कैसे हैं?",
    "Agent: मैं ठीक हूँ, आपकी कैसे मदद कर सकता हूँ?"
  ];

  return (
    <div id="voice-agent-demo" className="py-24 max-w-[1200px] mx-auto px-6 relative">
      <div className="cursor-card overflow-hidden bg-cur-surface-100 shadow-2xl relative">
        {/* Preview Badge */}
        <div className="absolute top-4 right-4 z-20">
          <div className="px-3 py-1 bg-cur-orange/10 border border-cur-orange text-cur-orange text-[11px] font-mono uppercase tracking-widest rounded-full animate-pulse">
            Preview Mode
          </div>
        </div>

        <div className="flex flex-col lg:flex-row min-h-[600px] opacity-70 grayscale-[0.3]">
          {/* Interaction Side */}
          <div className="flex-[3] p-16 flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-border-primary bg-cur-cream">
            <div className="relative mb-12">
              <button 
                onClick={() => signInWithGoogle()}
                className="group relative w-40 h-40 rounded-full flex items-center justify-center transition-all bg-cur-surface-300 border border-border-medium hover:border-border-strong shadow-lg"
              >
                <div className="flex flex-col items-center">
                  <svg className="w-16 h-16 text-cursor-dark opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
              </button>
            </div>

            <div className="text-center">
              <h2 className="section-heading !text-[28px] mb-3">Begin Conversation</h2>
              <p className="body-standard !text-[16px] max-w-[320px] mx-auto">
                Sign in to start a real-time multilingual session.
              </p>
              <button 
                onClick={() => signInWithGoogle()}
                className="mt-8 text-[13px] font-mono uppercase tracking-[0.2em] text-cur-orange hover:text-cur-error transition-colors"
              >
                Get Started →
              </button>
            </div>
          </div>

          {/* Timeline & Feedback Side */}
          <div className="flex-[4] p-16 flex flex-col grayscale">
            <div className="flex items-center justify-between mb-12">
              <span className="font-mono text-[11px] uppercase tracking-wider text-border-strong opacity-60">AI Timeline</span>
              <div className="flex gap-1.5 opacity-40">
                <div className="w-2 h-2 rounded-full bg-border-primary"></div>
                <div className="w-2 h-2 rounded-full bg-border-primary"></div>
                <div className="w-2 h-2 rounded-full bg-border-primary"></div>
              </div>
            </div>

            <div className="flex-1 space-y-12">
              <div className="relative">
                <div className="absolute left-[7px] top-6 bottom-[-48px] w-[2px] bg-border-primary"></div>
                
                <div className="space-y-12">
                  <TimelineStep label="Grep" desc="Dialect tokenization" color="#9fc9a2" />
                  <TimelineStep label="Think" desc="Contextual reasoning" color="#dfa88f" />
                  <TimelineStep label="Edit" desc="Bulbul v3 synthesis" color="#c0a8dd" />
                </div>
              </div>

              {/* Mock Context */}
              <div className="mt-16 pt-12 border-t border-border-primary opacity-40">
                <div className="font-mono text-[11px] mb-6 text-border-strong uppercase">Sample Context</div>
                <div className="space-y-4">
                  {transcripts.map((t, i) => (
                    <div key={i} className="flex gap-4 items-start">
                      <div className="font-mono text-[12px] mt-1 text-border-strong">
                        {t.split(':')[0]}
                      </div>
                      <div className="font-editorial text-[17px] leading-relaxed text-cursor-dark font-medium">
                        {t.split(':')[1]}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TimelineStep({ color, label, desc }: { color: string, label: string, desc: string }) {
  return (
    <div className="flex gap-6 opacity-40">
      <div className="relative z-10 w-4 h-4 rounded-full border-2 border-cur-cream bg-cur-dark flex items-center justify-center mt-1.5" />
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-[12px] font-bold">{label}</span>
        </div>
        <p className="font-sans text-[14px] text-border-strong leading-tight">{desc}</p>
      </div>
    </div>
  );
}
